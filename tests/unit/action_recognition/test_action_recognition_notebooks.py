# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# This test is based on the test suite implemented for Recommenders project
# https://github.com/Microsoft/Recommenders/tree/master/tests

import os
import papermill as pm
import pytest
import scrapbook as sb

# Unless manually modified, python3 should be
# the name of the current jupyter kernel
# that runs on the activated conda environment
KERNEL_NAME = "python3"
OUTPUT_NOTEBOOK = "output.ipynb"


@pytest.mark.notebooks
def test_00_notebook_run(action_recognition_notebooks):
    notebook_path = action_recognition_notebooks["00"]
    pm.execute_notebook(
        notebook_path,
        OUTPUT_NOTEBOOK,
        parameters=dict(PM_VERSION=pm.__version__),
        kernel_name=KERNEL_NAME,
    )

    nb_output = sb.read_notebook(OUTPUT_NOTEBOOK)
    # TODO add some asserts like below
    # assert nb_output.scraps["predicted_label"].data == "coffee_mug"
    # assert nb_output.scraps["predicted_confidence"].data > 0.5


@pytest.mark.notebooks
def test_01_notebook_run(action_recognition_notebooks):
    # TODO - this notebook relies on downloading hmdb51, so pass for now
    pass

    # notebook_path = classification_notebooks["01"]
    # pm.execute_notebook(
    #     notebook_path,
    #     OUTPUT_NOTEBOOK,
    #     parameters=dict(PM_VERSION=pm.__version__),
    #     kernel_name=KERNEL_NAME,
    # )

    # nb_output = sb.read_notebook(OUTPUT_NOTEBOOK)
    # TODO add some asserts like below
    # assert len(nb_output.scraps["training_accuracies"].data) == 1


@pytest.mark.notebooks
def test_02_notebook_run(action_recognition_notebooks):
    pass


@pytest.mark.notebooks
def test_10_notebook_run(action_recognition_notebooks):
    notebook_path = action_recognition_notebooks["10"]
    pm.execute_notebook(
        notebook_path,
        OUTPUT_NOTEBOOK,
        parameters=dict(PM_VERSION=pm.__version__),
        kernel_name=KERNEL_NAME,
    )

    nb_output = sb.read_notebook(OUTPUT_NOTEBOOK)
    # TODO add some asserts like below
    # assert len(nb_output.scraps["training_accuracies"].data) == 1
