# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# This test is based on the test suite implemented for Recommenders project
# https://github.com/Microsoft/Recommenders/tree/master/tests

import os
import glob
import papermill as pm
import pytest
import shutil

# Unless manually modified, python3 should be
# the name of the current jupyter kernel
# that runs on the activated conda environment
KERNEL_NAME = "cvbp"
OUTPUT_NOTEBOOK = "output.ipynb"


@pytest.mark.notebooks
def test_00_notebook_run(classification_notebooks):
    notebook_path = classification_notebooks["00_webcam"]
    pm.execute_notebook(
        notebook_path,
        OUTPUT_NOTEBOOK,
        parameters=dict(PM_VERSION=pm.__version__),
        kernel_name=KERNEL_NAME,
    )


@pytest.mark.notebooks
def test_01_notebook_run(classification_notebooks, tiny_ic_data_path):
    notebook_path = classification_notebooks["01_training_introduction"]
    pm.execute_notebook(
        notebook_path,
        OUTPUT_NOTEBOOK,
        parameters=dict(
            PM_VERSION=pm.__version__, DATA_PATH=tiny_ic_data_path
        ),
        kernel_name=KERNEL_NAME,
    )


@pytest.mark.notebooks
def test_02_notebook_run(classification_notebooks, tiny_ic_data_path):
    notebook_path = classification_notebooks["02_training_accuracy_vs_speed"]
    pm.execute_notebook(
        notebook_path,
        OUTPUT_NOTEBOOK,
        parameters=dict(
            PM_VERSION=pm.__version__,
            DATA_PATH=tiny_ic_data_path,
            MODEL_TYPE="fast_inference",  # options: ['fast_inference', 'high_accuracy', 'small_size']
            EPOCHS_HEAD=1,
            EPOCHS_BODY=1,
        ),
        kernel_name=KERNEL_NAME,
    )


@pytest.mark.notebooks
def test_10_notebook_run(classification_notebooks, tiny_ic_data_path):
    notebook_path = classification_notebooks["10_image_annotation"]
    pm.execute_notebook(
        notebook_path,
        OUTPUT_NOTEBOOK,
        parameters=dict(
            PM_VERSION=pm.__version__,
            IM_DIR=os.path.join(tiny_ic_data_path, "can"),
        ),
        kernel_name=KERNEL_NAME,
    )


@pytest.mark.notebooks
def test_11_notebook_run(classification_notebooks, tiny_ic_data_path):
    notebook_path = classification_notebooks["11_exploring_hyperparameters"]
    pm.execute_notebook(
        notebook_path,
        OUTPUT_NOTEBOOK,
        parameters=dict(
            PM_VERSION=pm.__version__,
            DATA=[tiny_ic_data_path],
            REPS=1,
            LEARNING_RATES=[1e-3],
            IM_SIZES=[199],
            EPOCHS=[1],
        ),
        kernel_name=KERNEL_NAME,
    )


@pytest.mark.notebooks
def skip_test_21_notebook_run(classification_notebooks, tiny_ic_data_path):
    """ NOTE - this function is intentionally prefixed with 'skip' so that
    pytests bypasses this function
    """
    notebook_path = classification_notebooks[
        "21_deployment_on_azure_container_instances"
    ]
    pm.execute_notebook(
        notebook_path,
        OUTPUT_NOTEBOOK,
        parameters=dict(
            PM_VERSION=pm.__version__, DATA_PATH=tiny_ic_data_path
        ),
        kernel_name=KERNEL_NAME,
    )
    try:
        os.remove("myenv.yml")
    except OSError:
        pass
    try:
        os.remove("score.py")
    except OSError:
        pass

    try:
        os.remove("output.ipynb")
    except OSError:
        pass

    # There should be only one file, but the name may be changed
    file_list = glob.glob("./*.pkl")
    for filePath in file_list:
        try:
            os.remove(filePath)
        except OSError:
            pass

    # TODO should use temp folder for safe cleanup. Notebook should accept the folder paths via papermill param.
    shutil.rmtree(os.path.join(os.getcwd(), "azureml-models"))
    shutil.rmtree(os.path.join(os.getcwd(), "models"))
    shutil.rmtree(os.path.join(os.getcwd(), "outputs"))
