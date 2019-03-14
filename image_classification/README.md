# Image classification

This directory provides examples and best practices for building image classification systems. We use [fast.ai](https://github.com/fastai/fastai) heavily, since it has rich feature support and ... .

See also fast.ai's [documentation](https://docs.fast.ai/) and most recent [course](https://github.com/fastai/course-v3) for more explanations and code examples.

## Getting Started

To setup on your local machine:
1. Install Anaconda with Python >= 3.6. [Miniconda](https://conda.io/miniconda.html) is a quick way to get started.
1. Clone the repository
    ```
    git clone https://github.com/Microsoft/ComputerVisionBestPractices
    cd ComputerVisionBestPractices
    ```
1. Install the conda environment
    ```
    conda env create -f environment.yml
    ```
1. Activate the conda environment and register it with Jupyter:
    ```
    conda activate cvbp
    python -m ipykernel install --user --name cvbp --display-name "Python (cvbp)"
    ```
1. Start the Jupyter notebook server
    ```
    cd notebooks
    jupyter notebook
    ```
2. Run the [Webcam Image Classification Notebook](notebooks/00_webcam.ipynb) notebook under the notebooks folder. Make sure to change the kernel to "Python (cvbp)".

## Coding guidelines

Variable naming should be consistent, i.e. an image should always be called "im" and not "i", "img", "imag", "image", etc. Since we take a strong dependency on fast.ai, variable naming should follow the standards of fast.ai which are described in this [abbreviation guide](https://docs.fast.ai/dev/abbr.html). The one exception to this guide is that variable names should be as self-explanatory as possible. For example, the meaning of the variable "batch_size" is clear, compared to using "bs" to refer to batch size.

See also the more general [coding guidelines](https://github.com/Microsoft/Recommenders/wiki/Coding-Guidelines) in the "Microsoft/Recommenders" github repo.

The main variables and abbreviations are given in the table below:

| Abbreviation | Description |
| ------------ | ----------- |
| im                     | Image
| fig                    | Figure
| pt                     | 2D point (column,row)
| rect                   | Rectangle (order: left, top, right, bottom)
| width,height (or w/h)  | Image dimensions
| scale                  | Image up/downscaling factor
| angle                  | Rotation angle in degree
| table                  | 2D row/column matrix implemented using a list of lists
| row,list1D             | Single row in a table, i.e. single 1D-list
| rowItem                | Single item in a row
| line,string            | Single string
| lines,strings          | List of strings
| list1D                 | List of items, not necessarily strings
| -s    | Multiple of something (plural) should be indicated by appending an "s" to an abbreviation.

## Notebooks

We provide several notebooks to show how image classification algorithms can be designed, evaluated and operationalized.

1. [Webcam](.notebooks/00_webcam.ipynb)

   An introduction to image classification.

1. [Intro to training image classification models](.notebooks/01_training_introduction.ipynb)

   Introduction to training an Image classification model.

1. TODO

## Appendix 

1. [Fastai course v3](https://github.com/fastai/course-v3)


