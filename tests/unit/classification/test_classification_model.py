# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import numpy as np
from torch import tensor
from fastai.metrics import accuracy, error_rate
from fastai.vision import cnn_learner, models
from fastai.vision import ImageList, imagenet_stats
from utils_cv.classification.model import (
    get_optimal_threshold,
    get_preds,
    hamming_accuracy,
    model_to_learner,
    TrainMetricsRecorder,
    zero_one_accuracy,
)


def test_hamming_accuracy_function(multilabel_result):
    """ Test the hamming loss evaluation metric function. """
    y_pred, y_true = multilabel_result
    assert hamming_accuracy(y_pred, y_true) == tensor(1.0 - 0.1875)
    assert hamming_accuracy(y_pred, y_true, sigmoid=True) == tensor(
        1.0 - 0.375
    )
    assert hamming_accuracy(y_pred, y_true, threshold=1.0) == tensor(
        1.0 - 0.625
    )


def test_zero_one_accuracy_function(multilabel_result):
    """ Test the zero-one loss evaluation metric function. """
    y_pred, y_true = multilabel_result
    assert zero_one_accuracy(y_pred, y_true) == tensor(1.0 - 0.75)
    assert zero_one_accuracy(y_pred, y_true, sigmoid=True) == tensor(
        1.0 - 0.75
    )
    assert zero_one_accuracy(y_pred, y_true, threshold=1.0) == tensor(
        1.0 - 1.0
    )


def test_get_optimal_threshold(multilabel_result):
    """ Test the get_optimal_threshold function. """
    y_pred, y_true = multilabel_result
    assert get_optimal_threshold(hamming_accuracy, y_pred, y_true) == 0.05
    assert (
        get_optimal_threshold(
            hamming_accuracy, y_pred, y_true, thresholds=np.linspace(0, 1, 11)
        )
        == 0.1
    )
    assert get_optimal_threshold(zero_one_accuracy, y_pred, y_true) == 0.05
    assert (
        get_optimal_threshold(
            zero_one_accuracy, y_pred, y_true, thresholds=np.linspace(0, 1, 11)
        )
        == 0.1
    )


def test_model_to_learner():
    # Test if the function loads an ImageNet model (ResNet) trainer
    learn = model_to_learner(models.resnet34(pretrained=True))
    assert len(learn.data.classes) == 1000  # Check Image net classes
    assert isinstance(learn.model, models.ResNet)

    # Test with SqueezeNet
    learn = model_to_learner(models.squeezenet1_0())
    assert len(learn.data.classes) == 1000
    assert isinstance(learn.model, models.SqueezeNet)


@pytest.fixture
def tiny_ic_data(tiny_ic_data_path):
    """ Returns tiny ic data bunch """
    return (
        ImageList.from_folder(tiny_ic_data_path)
        .split_by_rand_pct(valid_pct=0.2, seed=10)
        .label_from_folder()
        .transform(size=299)
        .databunch(bs=16)
        .normalize(imagenet_stats)
    )


def test_train_metrics_recorder(tiny_ic_data):
    model = models.resnet18
    lr = 1e-4
    epochs = 2

    def test_callback(learn):
        tmr = TrainMetricsRecorder(learn)
        learn.callbacks.append(tmr)
        learn.unfreeze()
        learn.fit(epochs, lr)
        return tmr

    # multiple metrics
    learn = cnn_learner(tiny_ic_data, model, metrics=[accuracy, error_rate])
    cb = test_callback(learn)
    assert len(cb.train_metrics) == len(cb.valid_metrics) == epochs
    assert (
        len(cb.train_metrics[0]) == len(cb.valid_metrics[0]) == 2
    )  # we used 2 metrics

    # no metrics
    learn = cnn_learner(tiny_ic_data, model)
    cb = test_callback(learn)
    assert len(cb.train_metrics) == len(cb.valid_metrics) == 0  # no metrics

    # no validation set
    learn = cnn_learner(tiny_ic_data, model, metrics=accuracy)
    learn.data.valid_dl = None
    cb = test_callback(learn)
    assert len(cb.train_metrics) == epochs
    assert len(cb.train_metrics[0]) == 1  # we used 1 metrics
    assert len(cb.valid_metrics) == 0  # no validation

    
def test_get_preds(tiny_ic_data):
    model = models.resnet18
    lr = 1e-4
    epochs = 1
    
    learn = cnn_learner(tiny_ic_data, model)
    learn.fit(epochs, lr)
    pred_outs = get_preds(learn, tiny_ic_data.valid_dl)
    assert len(pred_outs[0]) == len(tiny_ic_data.valid_ds)
