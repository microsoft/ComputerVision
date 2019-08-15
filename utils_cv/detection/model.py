# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import numpy as np
from typing import List, Tuple, Union
from pathlib import Path
from functools import partial

from PIL import Image
import cv2
import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torch.utils.data import Dataset, DataLoader
import matplotlib.pyplot as plt

from .references.transforms import RandomHorizontalFlip, Compose, ToTensor
from .references.engine import train_one_epoch, evaluate
from .references.utils import collate_fn
from .references.coco_eval import CocoEvaluator
from .plot import BoundingBoxParams, plot_boxes, plot_grid


def get_bounding_boxes(
    pred: List[dict], threshold: int = 0.6
) -> Tuple[List[int], List[List[int]]]:
    """ Gets the bounding boxes and labels from a prediction given a threshold.

    Args:
        pred: the output of passing in an image to torchvision's FasterRCNN
        model
        threshold: the minimum threshold to accept.

    Return:
        a list of labels and bounding boxes that pass the minimum threshold.
    """
    pred_labels = list(pred[0]["labels"].cpu().numpy())
    pred_boxes = list(pred[0]["boxes"].detach().cpu().numpy().astype(np.int32))
    pred_scores = list(pred[0]["scores"].cpu().numpy())

    qualified_labels = []
    qualified_boxes = []
    for label, box, score in zip(pred_labels, pred_boxes, pred_scores):
        if score > threshold:
            qualified_labels.append(label)
            qualified_boxes.append(box)
    return qualified_labels, qualified_boxes


def get_transform(train: bool) -> List[object]:
    """ Gets basic the transformations to apply to images.

    Args:
        train: whether or not we are getting transformations for the training
        set.

    Returns:
        A list of transforms to apply.
    """
    transforms = []
    transforms.append(ToTensor())
    if train:
        transforms.append(RandomHorizontalFlip(0.5))
    return Compose(transforms)


def get_pretrained_fasterrcnn(num_classes: int) -> nn.Module:
    """ Gets a pretrained FasterRCNN model

    Args:
        num_classes: the number of classes to be detected

    Returns
        The model to fine-tine/inference with
    """
    # load a model pre-trained pre-trained on COCO
    model = fasterrcnn_resnet50_fpn(pretrained=True)

    # get number of input features for the classifier
    in_features = model.roi_heads.box_predictor.cls_score.in_features

    # replace the pre-trained head with a new one
    # that has num_classes which is based on the dataset
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    return model


class DetectionLearner:
    """ Detection Learner for Object Detection"""

    def __init__(
        self,
        dataset: Dataset,
        lr: float,
        train_ratio: float = 0.8,
        batch_size: int = 2,
        model: nn.Module = None,
        momentum: float = 0.9,
        weight_decay: float = 0.0005,
    ):
        """ Initialize leaner object. """
        self.device = (
            torch.device("cuda")
            if torch.cuda.is_available()
            else torch.device("cpu")
        )
        self.model = model
        self.dataset = dataset
        self.lr = lr
        self.batch_size = batch_size
        self.momentum = momentum
        self.weight_decay = weight_decay

        # setup datasets (train_ds, test_ds, train_dl, test_dl)
        self._setup_data(dataset, train_ratio=train_ratio)

        # setup model, default to fasterrcnn
        if self.model is None:
            self.model = get_pretrained_fasterrcnn(len(dataset.categories)).to(
                self.device
            )

        # construct our optimizer
        params = [p for p in self.model.parameters() if p.requires_grad]
        self.optimizer = torch.optim.SGD(
            params,
            lr=self.lr,
            momentum=self.momentum,
            weight_decay=self.weight_decay,
        )

        # and a learning rate scheduler
        self.lr_scheduler = torch.optim.lr_scheduler.StepLR(
            self.optimizer, step_size=3, gamma=0.1
        )

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        raise AttributeError(
            "'{}' object has no attribute '{}'".format(
                type(self).__name__, attr
            )
        )

    def _setup_data(self, dataset: Dataset, train_ratio: float = 0.8):
        """ create training and validation data loaders
        """
        self.train_ds, self.test_ds = dataset.split_train_test(
            train_ratio=train_ratio
        )

        self.train_dl = DataLoader(
            self.train_ds,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=4,
            collate_fn=collate_fn,
        )

        self.test_dl = DataLoader(
            self.test_ds,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=4,
            collate_fn=collate_fn,
        )

    def fit(self, epochs: int, print_freq: int = 10) -> None:
        """ The main training loop. """
        self.losses = []
        self.epochs = epochs
        for epoch in range(self.epochs):
            # train for one epoch, printing every 10 iterations
            logger = train_one_epoch(
                self.model,
                self.optimizer,
                self.train_dl,
                self.device,
                epoch,
                print_freq=print_freq,
            )
            self.losses.append(logger.meters["loss"].median)

            # update the learning rate
            self.lr_scheduler.step()

            # evaluate
            self.evaluate(dl=self.train_dl)

    def plot_losses(self, figsize: Tuple[int, int] = (10, 5)) -> None:
        """ Plot training loss from fitting. """
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        ax.set_xlim([0, self.epochs - 1])
        ax.set_xticks(range(0, self.epochs))
        ax.set_title("Loss over epochs")
        ax.set_xlabel("epochs")
        ax.set_ylabel("loss")
        ax.plot(self.losses)

    def evaluate(self, dl: DataLoader = None) -> CocoEvaluator:
        """ eval code on validation/test set. """
        if dl is None:
            dl = self.test_dl
        return evaluate(self.model, dl, device=self.device)

    def get_model(self) -> nn.Module:
        """ returns the model object. """
        return self.model

    def inference(self, im_path: Union[str, Path]):
        """ Performs inferencing on an image path. """
        im = Image.open(im_path)
        transform = transforms.Compose([transforms.ToTensor()])
        im = transform(im).cuda()
        model = self.get_model().eval()  # eval mode
        with torch.no_grad():
            pred = model([im])
        return pred

    def show_detection_vs_ground_truth(self, idx: int, ax: plt.axes) -> None:
        """ Plots the bounding box predictions and ground truth

        Args:
            idx: the index of the dataset to visualize
            ax: axes to draw on

        Returns nothing but plots graph.
        """
        im_path = (
            self.dataset.root
            / self.dataset.image_folder
            / self.dataset.ims[idx]
        )
        im = cv2.imread(str(im_path))

        # plot prediction boxes
        pred = self.inference(im_path)
        pred_labels, pred_boxes = get_bounding_boxes(pred)
        pred_params = BoundingBoxParams(rect_color=(255, 0, 0), text_size=0)
        im = plot_boxes(
            im,
            pred_boxes,
            [self.dataset.categories[l] for l in pred_labels],
            bbox_params=pred_params,
        )

        # plot ground truth boxes
        ground_truth_params = BoundingBoxParams(
            rect_color=(0, 255, 0), text_size=0
        )
        boxes, categories, im_path = self.dataset.get_image_features(idx)
        im = plot_boxes(im, boxes, categories, bbox_params=ground_truth_params)

        # show image
        ax.set_xticks([])
        ax.set_yticks([])
        ax.imshow(im)

    def show_preds(self, ds: Dataset = None, rows: int = 1) -> None:
        """ Show batch of predictions against ground truth.

        Args:
            ds: the datset to use, by default, use test_ds
            rows: rows to predict

        Returns nothing
        """
        if ds is None:
            ds = self.test_ds

        # setup iterator if not yet setup
        if not hasattr(self, "ds_iterator"):
            self.ds_iterator = iter(ds.indices)

        plot_grid(
            self.show_detection_vs_ground_truth,
            partial(next, self.ds_iterator),
            rows=rows,
        )