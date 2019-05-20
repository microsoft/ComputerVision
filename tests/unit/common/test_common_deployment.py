# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import sys

sys.path.extend([".", "..", "../..", "../../.."])

from utils_cv.common.data import root_path
from utils_cv.common.deployment import generate_yaml


def test_generate_yaml():
    """Tests creation of deployment-specific yaml file
    from existing image_classification/environment.yml"""
    generate_yaml(
        directory=os.path.join(root_path(), "classification"),
        ref_filename="environment.yml",
        needed_libraries=["fastai", "pytorch"],
        conda_filename="mytestyml.yml",
    )

    assert os.path.exists(os.path.join(os.getcwd(), "mytestyml.yml"))
    os.remove(os.path.join(os.getcwd(), "mytestyml.yml"))
