# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import torch.cuda as cuda
from utils_ic.gpu_utils import gpu_info


def test_gpu_info():
    """
    Test if exist_ok is false and (file exists, file does not exist)
    """
    gpus = gpu_info()
    # Check if torch.cuda returns the same number of gpus
    assert cuda.device_count() == len(gpus)

    for i in range(len(gpus)):
        # Check if torch.cuda returns the same device name
        assert gpus[i]['device_name'] == cuda.get_device_name(i)
        # Total memory should be grater than used-memory
        assert int(gpus[i]['total_memory']) > int(gpus[i]['used_memory'])
