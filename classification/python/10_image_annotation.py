#!/usr/bin/env python
# coding: utf-8

# <i>Copyright (c) Microsoft Corporation. All rights reserved.</i>
# 
# <i>Licensed under the MIT License.</i>

# # Image annotation UI

# Open-source annotation tools for object detection and for image segmentation exist, however for image classification we were not able to find a good program. Hence this notebook provides a simple UI to label images. Each image can be annotated with one or multiple classes, or marked as "Exclude" to indicate that the image should not be used for model training or evaluation. 
# 
# Note that, for single class annotation tasks, one does not need any UI but can instead simply drag-and-drop images into separate folder for the respective classes. 
# 
# See the [FAQ.md](../FAQ.md) for a brief discussion on how to scrape images from the internet.

# In[1]:


# Ensure edits to libraries are loaded and plotting is shown in the notebook.
get_ipython().run_line_magic('reload_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')
get_ipython().run_line_magic('matplotlib', 'inline')


# In[2]:


import os
import sys
sys.path.append("../")
from utils_ic.anno_utils import AnnotationWidget
from utils_ic.datasets import unzip_url, Urls


# Set parameters: location of the images to annotate, and path where to save the annotations. Here `unzip_url` is used to download example data if not already present, and set the path.

# In[3]:


IM_DIR = os.path.join((unzip_url(Urls.fridge_objects_path, exist_ok=True)), 'can')
ANNO_PATH = "cvbp_ic_annotation.txt"
print(f"Using images in directory: {IM_DIR}.")


# Start the UI. Check the "Allow multi-class labeling" box to allow for images to be annotated with multiple classes. When in doubt what the annotation for an image should be, or for any other reason (e.g. blur or over-exposure), mark an image as "EXCLUDE". All annotations are saved to (and loaded from) a pandas dataframe with path specified in `anno_path`. Note that the toy dataset in this notebook only contains images of cans. 
# 
# <img src="media/anno_ui.jpg" width="500px" />

# In[4]:


w_anno_ui = AnnotationWidget(
    labels       = ["can", "carton", "milk_bottle", "water_bottle"],
    im_dir       = IM_DIR,
    anno_path    = ANNO_PATH,
    im_filenames = None #Set to None to annotate all images in IM_DIR
)

display(w_anno_ui.show())


# Below is an example how to create a fast.ai ImageList object using the ground truth annotations generated by the AnnotationWidget. Fast.ai does not support the exclude flag, hence we remove these images before calling the `from_df()` and `label_from_df()` functions. 
# For this example, we create a toy annotation file at `example_annotation.csv` rather than using `ANNO_PATH`. 

# In[5]:


get_ipython().run_cell_magic('writefile', 'example_annotation.csv', 'IM_FILENAME\tEXCLUDE\tLABELS\n10.jpg\tFalse\tcan\n11.jpg\tFalse\tcan,carton\n12.jpg\tTrue\t\n13.jpg\tFalse\tcarton\n15.jpg\tFalse\tcarton,milk_bottle\n16.jpg\tFalse\tcan\n17.jpg\tTrue\t\n18.jpg\tFalse\tcan')


# In[6]:


import pandas as pd
from fastai.vision import ImageList,ImageDataBunch

# Load annotation, discard excluded images, and convert to format fastai expects
data = []
with open("example_annotation.csv",'r') as f:
    for line in f.readlines()[1:]:
        vec = line.strip().split("\t")
        exclude = vec[1]=="True"
        if not exclude and len(vec)>2:
            data.append((vec[0], vec[2]))

df = pd.DataFrame(data, columns = ["name", "label"])
display(df)

data = (ImageList.from_df(path=IM_DIR, df = df)
       .split_by_rand_pct(valid_pct=0.5)
       .label_from_df(cols='label', label_delim=','))
print(data)

