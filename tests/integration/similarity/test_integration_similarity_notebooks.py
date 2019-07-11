# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import papermill as pm
import pytest
import scrapbook as sb
from torch.cuda import is_available

from utils_cv.common.gpu import linux_with_gpu

# Parameters
KERNEL_NAME = "cv"
OUTPUT_NOTEBOOK = "output.ipynb"


@pytest.mark.notebooks
def test_01_notebook_run(similarity_notebooks):
    if linux_with_gpu():
        notebook_path = similarity_notebooks["01"]
        pm.execute_notebook(
            notebook_path,
            OUTPUT_NOTEBOOK,
            parameters=dict(PM_VERSION=pm.__version__),
            kernel_name=KERNEL_NAME,
        )

        nb_output = sb.read_notebook(OUTPUT_NOTEBOOK)
        assert nb_output.scraps["median_rank"].data <= 10
