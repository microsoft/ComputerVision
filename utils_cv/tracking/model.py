# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import argparse
from collections import OrderedDict, defaultdict
from copy import deepcopy
import glob
import requests
import os
import os.path as osp
import tempfile
from typing import Dict, List, Optional, Tuple

import torch
import torch.cuda as cuda
import torch.nn as nn
from torch.utils.data import DataLoader

import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import motmetrics as mm

from .references.fairmot.datasets.dataset.jde import LoadImages, LoadVideo
from .references.fairmot.models.model import (
    create_model,
    load_model,
    save_model,
)
from .references.fairmot.tracker.multitracker import JDETracker
from .references.fairmot.tracking_utils.evaluation import Evaluator
from .references.fairmot.trains.train_factory import train_factory

from .bbox import TrackingBbox
from .dataset import TrackingDataset, boxes_to_mot
from .opts import opts
from .plot import draw_boxes, assign_colors
from ..common.gpu import torch_device


def _get_gpu_str():
    if cuda.is_available():
        devices = [str(x) for x in range(cuda.device_count())]
        return ",".join(devices)
    else:
        return "-1"  # cpu


def write_video(results: Dict[int, List[TrackingBbox]], 
                input_video: str, 
                output_video: str) -> None:
    """ 
    Plot the predicted tracks on the input video. Write the output to {output_path}.

    Args:
        results: dictionary mapping frame id to a list of predicted TrackingBboxes
        input_video: path to the input video
        output_video: path to write out the output video
    """
    results = OrderedDict(sorted(results.items()))
    # read video and initialize new tracking video
    video = cv2.VideoCapture()
    video.open(input_video)

    image_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    image_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"MP4V")
    frame_rate = int(video.get(cv2.CAP_PROP_FPS))
    writer = cv2.VideoWriter(
        output_video, fourcc, frame_rate, (image_width, image_height)
    )

    # assign bbox color per id
    unique_ids = list(
        set([bb.track_id for frame in results.values() for bb in frame])
    )
    color_map = assign_colors(unique_ids)

    # create images and add to video writer, adapted from https://github.com/ZQPei/deep_sort_pytorch
    frame_idx = 0
    while video.grab():
        _, cur_image = video.retrieve()
        cur_tracks = results[frame_idx]
        if len(cur_tracks) > 0:
            cur_image = draw_boxes(cur_image, cur_tracks, color_map)
        writer.write(cur_image)
        frame_idx += 1

    print(f"Output saved to {output_video}.")


def savetxt_results(results: Dict[int, List[TrackingBbox]],
                    exp_name: str = 'results',
                    root_path: str = None,
                    result_filename: str = 'results.txt') -> str:
    """Save tracking results to txt in tmp directory or provided path.

    Args:
        results: prediction results from predict() function, i.e. Dict[int, List[TrackingBbox]]
        exp_name: subfolder for each experiment
        root_path: results saved root path. Default: None
        result_filename: saved prediction results txt file; End with '.txt'
    Returns:
        result_path: saved prediction results txt file path
    """
    if not root_path:
        with tempfile.TemporaryDirectory() as tmpdir1:
            os.makedirs(osp.join(tmpdir1, exp_name))
            result_path = osp.join(tmpdir1, exp_name, result_filename)
    else:
        result_path = osp.join(root_path, exp_name, result_filename)

    # Save results in MOT format for evaluation            
    bboxes_mot = boxes_to_mot(results)
    np.savetxt(result_path, bboxes_mot, delimiter=",", fmt="%s")
    return result_path


def evaluate_mot(gt_root_path: str,
                 exp_name: str,
                 result_path: str) -> object:
    """ eval code that calls on 'motmetrics' package in referenced FairMOT script, to produce MOT metrics on inference, given ground-truth.
    Args:
        gt_root_path: path of dataset containing GT annotations in MOTchallenge format (xywh)
        exp_name: subfolder for each experiment
        result_path: saved prediction results txt file path
    Returns:
        mot_accumulator: MOTAccumulator object from pymotmetrics package
    """
    # Implementation inspired from code found here: https://github.com/ifzhang/FairMOT/blob/master/src/track.py
    evaluator = Evaluator(gt_root_path, exp_name, "mot")

    # Run evaluation using pymotmetrics package
    mot_accumulator = evaluator.eval_file(result_path)

    return mot_accumulator


def mot_summary(accumulators: list,
                exp_names: list) -> str:
    """Given a list of MOTAccumulators, get total summary by method in 'motmetrics', containing metrics scores

    Args:
        accumulators: list of MOTAccumulators
        exp_names: list of experiment names (str) corresponds to MOTAccumulators
    Returns:
        strsummary: pandas.DataFrame output by method in 'motmetrics', containing metrics scores
    """
    metrics = mm.metrics.motchallenge_metrics
    mh = mm.metrics.create()

    summary = Evaluator.get_summary(accumulators, exp_names, metrics)
    strsummary = mm.io.render_summary(
        summary,
        formatters=mh.formatters,
        namemap=mm.io.motchallenge_metric_names
    )

    return strsummary


class TrackingLearner(object):
    """Tracking Learner for Multi-Object Tracking"""

    def __init__(
            self,
            dataset: Optional[TrackingDataset] = None,
            model_path: Optional[str] = None,
            arch: str = "dla_34",
            head_conv: int = None,
    ) -> None:
        """
        Initialize learner object.

        Defaults to the FairMOT model.

        Args:
            dataset: optional dataset (required for training)
            model_path: optional path to pretrained model (defaults to all_dla34.pth)
            arch: the model architecture
                Supported architectures: resdcn_34, resdcn_50, resfpndcn_34, dla_34, hrnet_32
            head_conv: conv layer channels for output head. None maps to the default setting.
                Set 0 for no conv layer, 256 for resnets, and 256 for dla
        """
        self.opt = opts()
        self.opt.arch = arch
        self.opt.head_conv = head_conv if head_conv else -1
        self.opt.gpus = _get_gpu_str()
        self.opt.device = torch_device()

        self.dataset = dataset
        self.model = None
        self._init_model(model_path)

    def _init_model(self, model_path) -> None:
        """
        Initialize the model.

        Args:
            model_path: optional path to pretrained model (defaults to all_dla34.pth)
        """
        if not model_path:
            model_path = osp.join(self.opt.root_dir, "models", "all_dla34.pth")
        assert osp.isfile(
            model_path
        ), f"Model weights not found at {model_path}"

        self.opt.load_model = model_path

    def fit(
            self, lr: float = 1e-4, lr_step: str = "20,27", num_epochs: int = 30
    ) -> None:
        """
        The main training loop.

        Args:
            lr: learning rate for batch size 32
            lr_step: when to drop learning rate by 10
            num_epochs: total training epochs

        Raise:
            Exception if dataset is undefined
        
        Implementation inspired from code found here: https://github.com/ifzhang/FairMOT/blob/master/src/train.py
        """
        if not self.dataset:
            raise Exception("No dataset provided")

        opt_fit = deepcopy(self.opt)  # copy opt to avoid bug
        opt_fit.lr = lr
        opt_fit.lr_step = lr_step
        opt_fit.num_epochs = num_epochs

        # update dataset options
        opt_fit.update_dataset_info_and_set_heads(self.dataset.train_data)

        # initialize dataloader
        train_loader = self.dataset.train_dl

        self.optimizer = torch.optim.Adam(self.model.parameters(), opt_fit.lr)
        start_epoch = 0
        self.model = create_model(self.opt.arch, self.opt.heads, self.opt.head_conv)
        self.model = load_model(self.model, opt_fit.load_model)

        Trainer = train_factory[opt_fit.task]
        trainer = Trainer(opt_fit.opt, self.model, self.optimizer)
        trainer.set_device(opt_fit.gpus, opt_fit.chunk_sizes, opt_fit.device)

        # initialize loss vars
        self.losses_dict = defaultdict(list)

        # training loop
        for epoch in range(
                start_epoch + 1, start_epoch + opt_fit.num_epochs + 1
        ):
            print(
                "=" * 5,
                f" Epoch: {epoch}/{start_epoch + opt_fit.num_epochs} ",
                "=" * 5,
            )
            self.epoch = epoch
            log_dict_train, _ = trainer.train(epoch, train_loader)
            for k, v in log_dict_train.items():
                print(f"{k}: {v}")
            if epoch in opt_fit.lr_step:
                lr = opt_fit.lr * (0.1 ** (opt_fit.lr_step.index(epoch) + 1))
                for param_group in optimizer.param_groups:
                    param_group["lr"] = lr

            # store losses in each epoch
            for k, v in log_dict_train.items():
                if k in ["loss", "hm_loss", "wh_loss", "off_loss", "id_loss"]:
                    self.losses_dict[k].append(v)

    def plot_training_losses(self, figsize: Tuple[int, int] = (10, 5)) -> None:
        """
        Plot training loss.  
        
        Args:
            figsize (optional): width and height wanted for figure of training-loss plot
        
        """
        fig = plt.figure(figsize=figsize)
        ax1 = fig.add_subplot(1, 1, 1)

        ax1.set_xlim([0, len(self.losses_dict["loss"]) - 1])
        ax1.set_xticks(range(0, len(self.losses_dict["loss"])))
        ax1.set_xlabel("epochs")
        ax1.set_ylabel("losses")

        ax1.plot(self.losses_dict["loss"], c="r", label="loss")
        ax1.plot(self.losses_dict["hm_loss"], c="y", label="hm_loss")
        ax1.plot(self.losses_dict["wh_loss"], c="g", label="wh_loss")
        ax1.plot(self.losses_dict["off_loss"], c="b", label="off_loss")
        ax1.plot(self.losses_dict["id_loss"], c="m", label="id_loss")

        plt.legend(loc="upper right")
        fig.suptitle("Training losses over epochs")

    def save(self, path) -> None:
        """
        Save the model to a specified path.
        """
        model_dir, _ = osp.split(path)
        os.makedirs(model_dir, exist_ok=True)

        save_model(path, self.epoch, self.model, self.optimizer)
        print(f"Model saved to {path}")

    def evaluate(
            self, results: Dict[int, List[TrackingBbox]], gt_root_path: str
    ) -> str:

        """ 
        Evaluate performance wrt MOTA, MOTP, track quality measures, global ID measures, and more,
        as computed by py-motmetrics on a single experiment. By default, use 'single_vid' as exp_name.

        Args:
            results: prediction results from predict() function, i.e. Dict[int, List[TrackingBbox]] 
            gt_root_path: path of dataset containing GT annotations in MOTchallenge format (xywh)
        Returns:
            strsummary: str output by method in 'motmetrics' package, containing metrics scores        
        """

        # Implementation inspired from code found here: https://github.com/ifzhang/FairMOT/blob/master/src/track.py
        result_path = savetxt_results(results, exp_name="single_vid")
        # Save tracking results in tmp
        mot_accumulator = evaluate_mot(gt_root_path, "single_vid", result_path)
        strsummary = mot_summary([mot_accumulator], ("single_vid",))
        return strsummary

    def eval_mot(self, conf_thres: float, track_buffer: int, im_size: Tuple[int, int], data_root: str,
                 seqs: list, result_root: str, exp_name: str, run_eval: bool = True) -> str:
        """
        Call the prediction function, saves the tracking results to txt file and provides the evaluation results with motmetrics format.
        Args:
            conf_thres: confidence thresh for tracking
            track_buffer: tracking buffer
            im_size: image resolution
            data_root: data root path
            seqs: list of video sequences subfolder names under MOT challenge data
            result_root: tracking result path
            exp_name: experiment name
            run_eval: if we evaluate on provided data
        Returns:
            strsummary: str output by method in 'motmetrics' package, containing metrics scores
        """
        eval_path = osp.join(result_root, exp_name)
        if not osp.exists(eval_path):
            os.makedirs(eval_path)
        accumulators = []
        for seq in seqs:
            im_path = osp.join(data_root, seq, 'img1')
            result_filename = '{}.txt'.format(seq)
            result_path = osp.join(result_root, exp_name, result_filename)
            with open(osp.join(data_root, seq, 'seqinfo.ini')) as seqinfo_file:
                meta_info = seqinfo_file.read()
            # frame_rate is set from seqinfo.ini by frameRate
            frame_rate = int(
                meta_info[meta_info.find('frameRate') + 10:meta_info.find('\nseqLength')])
            if not osp.exists(result_path):
                # Run tracking.
                eval_results = self.predict(
                    im_path,
                    conf_thres,
                    track_buffer,
                    im_size,
                    frame_rate)
                result_path = savetxt_results(eval_results, exp_name, result_root,
                                                   result_filename)
            print(f"Saved tracking results to {result_path}")
            if run_eval:
                # eval
                print(f"Evaluate seq: {seq}")
                mot_accumulator = evaluate_mot(data_root, seq, result_path)
                accumulators.append(mot_accumulator)
        if run_eval:
            return None
        else:
            strsummary = mot_summary(accumulators, seqs)
        return strsummary

    def predict(
            self,
            im_or_video_path: str,
            conf_thres: float = 0.6,
            det_thres: float = 0.3,
            nms_thres: float = 0.4,
            track_buffer: int = 30,
            min_box_area: float = 200,
            frame_rate: int = 30,
    ) -> Dict[int, List[TrackingBbox]]:
        """
        Run inference on an image or video path.

        Args:
            im_or_video_path: path to image(s) or video. Supports jpg, jpeg, png, tif formats for images.
                Supports mp4, avi formats for video. 
            conf_thres: confidence thresh for tracking
            det_thres: confidence thresh for detection
            nms_thres: iou thresh for nms
            track_buffer: tracking buffer
            min_box_area: filter out tiny boxes
            frame_rate: frame rate

        Returns a list of TrackingBboxes

        Implementation inspired from code found here: https://github.com/ifzhang/FairMOT/blob/master/src/track.py
        """
        opt_pred = deepcopy(self.opt)  # copy opt to avoid bug
        opt_pred.conf_thres = conf_thres
        opt_pred.det_thres = det_thres
        opt_pred.nms_thres = nms_thres
        opt_pred.track_buffer = track_buffer
        opt_pred.min_box_area = min_box_area

        # initialize tracker
        if self.model:
            tracker = JDETracker(
                opt_pred.opt, frame_rate=frame_rate, model=self.model
            )
        else:
            tracker = JDETracker(opt_pred.opt, frame_rate=frame_rate)

        # initialize dataloader
        dataloader = self._get_dataloader(im_or_video_path)

        frame_id = 0
        out = {}
        results = []
        for path, img, img0 in dataloader:
            blob = torch.from_numpy(img).cuda().unsqueeze(0)
            online_targets = tracker.update(blob, img0)
            online_bboxes = []
            for t in online_targets:
                tlwh = t.tlwh
                tlbr = t.tlbr
                tid = t.track_id
                vertical = tlwh[2] / tlwh[3] > 1.6
                if tlwh[2] * tlwh[3] > opt_pred.min_box_area and not vertical:
                    bb = TrackingBbox(
                        tlbr[1], tlbr[0], tlbr[3], tlbr[2], frame_id, tid
                    )
                    online_bboxes.append(bb)
            out[frame_id] = online_bboxes
            frame_id += 1

        return out

    def _get_dataloader(self, im_or_video_path: str) -> DataLoader:
        """
        Create a dataloader from images or video in the given path.

        Args:
            im_or_video_path: path to a root directory of images, or single video or image file.
                Supports jpg, jpeg, png, tif formats for images. Supports mp4, avi formats for video

        Return:
            Dataloader

        Raise:
            Exception if file format is not supported

        Implementation inspired from code found here: https://github.com/ifzhang/FairMOT/blob/master/src/lib/datasets/dataset/jde.py
        """
        im_format = [".jpg", ".jpeg", ".png", ".tif"]
        video_format = [".mp4", ".avi"]

        # if path is to a root directory of images

        if (
                osp.isdir(im_or_video_path)
                and len(
            list(
                filter(
                    lambda x: osp.splitext(x)[1].lower() in im_format,
                    sorted(glob.glob("%s/*.*" % im_or_video_path)),
                )
            )
        )
                > 0
        ):
            return LoadImages(im_or_video_path)
        # if path is to a single video file
        elif (
                osp.isfile(im_or_video_path)
                and osp.splitext(im_or_video_path)[1] in video_format
        ):
            return LoadVideo(im_or_video_path)
        # if path is to a single image file
        elif (
                osp.isfile(im_or_video_path)
                and osp.splitext(im_or_video_path)[1] in im_format
        ):
            return LoadImages(im_or_video_path)
        else:
            raise Exception("Image or video format not supported")
