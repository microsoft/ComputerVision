# Multi-Object Tracking

```diff
+ July 2020: This work is ongoing.
```

## Frequently asked questions

This document includes answers and information relating to common questions and topics regarding multi-object tracking. For more general Machine Learning questions, such as "How many training examples do I need?" or "How to monitor GPU usage during training?", see also the image classification [FAQ](https://github.com/microsoft/ComputerVision/blob/master/classification/FAQ.md).

* General
  * [What are the main evaluation metrics for tracking performance?](##What-are-the-commonly-used-evaluation-metrics)

* Data  
  * [How to annotate a video for evaluation?](#how-to-annotate-a-video-for-evaluation)
  * [What is the MOT Challenge format used by the evaluation package?](#What-is-the-MOT-Challenge-format-used-by-the-evaluation-package)
  * [List of popular MOT datasets](#Popular-MOT-Datasets)

* Training and Inference
  * [What are the main training parameters in FairMOT?](#what-are-the-main-training-parameters-in-FairMOT)
  * [How to improve training accuracy?](#how-to-improve-training-accuracy)
  * [What are the training losses for MOT using FairMOT?](#What-are-the-training-losses-for-MOT-using-FairMOT? )
  * [What are the main inference parameters in FairMOT?](#What-are-the-main-inference-parameters-in-FairMOT])

* MOT Challenge
  * [What is the MOT Challenge?](#What-is-the-MOT-Challenge)

* State-of-the-Art(SoTA) Technology
  * [What is the architecture of the FairMOT tracking algorithm?](#What-is-the-architecture-of-the-FairMOT-tracking-algorithm)
  * [What SoTA object detectors are used in tracking-by-detection trackers?](#What-SoTA-object-detectors-are-used-in-tracking-by-detection-trackers) 
  * [What SoTA feature extraction techniques are used in tracking-by-detection trackers?](#What-SoTA-feature-extraction-techniques-are-used-in-tracking-by-detection-trackers)
  * [What SoTA affinity and association techniques are used in tracking-by-detection trackers?](#What-SoTA-affinity-and-association-techniques-are-used-in-tracking-by-detection-trackers)
  * [What is the difference between online and offline (batch) tracking algorithms?](#What-is-the-difference-between-online-and-offline-tracking-algorithms)

* [Popular MOT Publications](#Popular-publications)



## General

### What are the commonly used evaluation metrics?
As multi-object-tracking is a complex CV task, there exists many different metrics to evaluate the tracking performance. Based on how they are computed, metrics can be event-based [CLEARMOT metrics](https://link.springer.com/content/pdf/10.1155/2008/246309.pdf) or [id-based metrics](https://arxiv.org/pdf/1609.01775.pdf). The main metrics used to gauge performance in the [MOT benchmarking challenge](https://motchallenge.net/results/MOT16/) include MOTA, IDF1, and ID-switch.

* MOTA (Multiple Object Tracking Accuracy) gauges overall accuracy performance using an event-based computation of how often mismatch occurs between the tracking results and ground-truth. MOTA contains the counts of FP (false-positive), FN (false negative), and id-switches (IDSW) normalized over the total number of ground-truth (GT) tracks.

<p align="center">
<img src="./media/eqn_mota.jpg" width="300" align="center"/>
</p>

* IDF1 measures overall performance with id-based computation of how long the tracker correctly identifies the target. It is the harmonic mean of identification precision (IDP) and recall (IDR).

<p align="center">
<img src="./media/eqn_idf1.jpg" width="450" align="center"/>
</p>

* ID-switch measures when the tracker incorrectly changes the ID of a trajectory. This is illustrated in the following figure: in the left box, person A and person B overlap and are not detected and tracked in frames 4-5. This results in an id-switch in frame 6, where person A is attributed the ID_2, which was previously tagged as person B. In another example in the right box, the tracker loses track of person A (initially identified as ID_1) after frame 3, and eventually identifies that person with a new ID (ID_2) in frame n, showing another instance of id-switch.

<p align="center">
<img src="./media/fig_tracksEval.jpg" width="600" align="center"/>
</p>



## Data

### How to annotate a video for evaluation?
Using an annotation tool, such as [VOTT](#https://github.com/microsoft/VoTT), one can create annotated ground truth data for a video. In the example below, annotating bounding boxes for each can, and then tagging each as `can_1` and `can_2` would create labeled data appropriate for use in a scenario of tracking the cans.
<p align="center">
<img src="./media/carcans_vott_ui.jpg" width="800" align="center"/>
</p>

Before annotating, it is important to correctly set the extraction rate to match that of the video. After annotation, you can export the annotation results into several forms, such as PASCAL VOC or .csv form. For the .csv format, VOTT would return the extracted frames, as well as a csv file containing the bounding box and id info: ``` [image] [xmin] [y_min] [x_max] [y_max] [label]```

### What is the MOT Challenge format used by the evaluation package?
The evaluation package, from  the [py-motmetrics](https://github.com/cheind/py-motmetrics) repository, requires the ground-truth data to be in [MOT challenge](https://motchallenge.net/) format, i.e.: 
```
[frame number] [id number] [bbox left] [bbox top] [bbox width] [bbox height][confidence score][class][visibility]
```
The last 3 columns can be set to -1 by default, for the purpose of ground-truth annotation.

### Popular MOT Datasets

<center>

| Name  | Year  | Duration |	# tracks/ids | Scene | Object type |
| ----- | ----- | -------- | --------------  | ----- |  ---------- |
| [MOT15](https://arxiv.org/pdf/1504.01942.pdf)| 2015 | 16 min | 1221 | Outdoor | Pedestrians |
| [MOT16/17](https://arxiv.org/pdf/1603.00831.pdf)| 2016 | 9 min | 1276 | Outdoor & indoor | Pedestrians & vehicles |
| [CVPR19/MOT20](https://arxiv.org/pdf/1906.04567.pdf)| 2019 | 26 min | 3833 | Crowded scenes | Pedestrians & vehicles |
| [PathTrack](http://openaccess.thecvf.com/content_ICCV_2017/papers/Manen_PathTrack_Fast_Trajectory_ICCV_2017_paper.pdf)| 2017 | 172 min | 16287 | YouTube people scenes | Persons |
| [Visdrone](https://arxiv.org/pdf/1804.07437.pdf)| 2019 | - | - | Outdoor view from drone camera | Pedestrians & vehicles |
| [KITTI](http://www.jimmyren.com/papers/rrc_kitti.pdf)| 2012 | 32 min | - | Traffic scenes from car camera | Pedestrians & vehicles |
| [UA-DETRAC](https://arxiv.org/pdf/1511.04136.pdf) | 2015 | 10h | 8200 | Traffic scenes | Vehicles |
| [CamNeT](https://vcg.ece.ucr.edu/sites/g/files/rcwecm2661/files/2019-02/egpaper_final.pdf) | 2015 | 30 min | 30 | Outdoor & indoor | Persons |

</center>

## Training and inference


### What are the main training parameters in FairMOT?

The main training parameters include batch size, learning rate and number of epochs. Additionally, FairMOT uses Torch's Adam algorithm as the default optimizer.


### How to improve training accuracy?

One can improve the training procedure by modifying the learning rate and number of epochs. As with most AI/ML training problems, this task is often specific to every learning scenario, but the general rules regarding under-training vs over-fitting apply.

### What are the training losses for MOT using FairMOT?

Losses generated by FairMOT include detection-specific losses (e.g. hm_loss, wh_loss, off_loss) and id-specific losses (id_loss). The overall loss (loss) is a weighted average of the detection-specific and id-specific losses, see the [FairMOT paper](https://arxiv.org/pdf/2004.01888v2.pdf).

### What are the main inference parameters in FairMOT?

- input_w and input_h: image resolution of the dataset video frames
- conf_thres, nms_thres, min_box_area: these thresholds used to filter out detections that do not meet the confidence level, nms level and size as per the user requirement;
- track_buffer: if a lost track is not matched for some number of frames as determined by this threshold, it is deleted, i.e. the id is not reused.

## MOT Challenge

### What is the MOT Challenge?
The [MOT Challenge](#https://motchallenge.net/) website hosts the most common benchmarking datasets for pedestrian MOT. Different datasets exist: MOT15, MOT16/17, MOT 19/20. These datasets contain many video sequences, with different tracking difficulty levels, with annotated ground-truth. Detections are also provided for optional use by the participating tracking algorithms.


## State-of-the-Art(SoTA) Technology

### What is the architecture of the FairMOT tracking algorithm?
It consists of a single encoder-decoder neural network that extracts high resolution feature maps of the image frame. As a one-shot tracker, it feeds into two parallel heads for predicting bounding boxes and re-id features respectively, see [source](https://arxiv.org/pdf/2004.01888v2.pdf): 
<p align="center">
<img src="./media/figure_fairMOTarc.jpg" width="800" align="center"/>
</p>

<center>

Source: [Zhang, 2020](https://arxiv.org/pdf/2004.01888v2.pdf)

</center>


### What SoTA object detectors are used in tracking-by-detection trackers?
The most popular object detectors used by SoTA tacking algorithms include: [Faster R-CNN](https://arxiv.org/pdf/1506.01497.pdf), [SSD](https://arxiv.org/pdf/1512.02325.pdf) and [YOLOv3](https://arxiv.org/pdf/1804.02767.pdf). Please see our [object detection FAQ page](../detection/faq.md) for more details.  


### What SoTA feature extraction techniques are used in tracking-by-detection trackers?
While older algorithms used local features, such as optical flow or regional features (e.g. color histograms, gradient-based features or covariance matrix), newer algorithms have deep-learning based feature representations. The most common deep-learning approaches, typically trained on re-id datasets, use classical CNNs to extract visual features. One such dataset is the [MARS dataset](http://www.liangzheng.com.cn/Project/project_mars.html). The following figure is an example of a CNN used for MOT by the [DeepSORT tracker](https://arxiv.org/pdf/1703.07402.pdf):
        <p align="center">
        <img src="./media/figure_DeepSortCNN.jpg" width="600" align="center"/>
        </p>
Newer deep-learning approaches include Siamese CNN networks, LSTM networks, or CNN with correlation filters. In Siamese CNN networks, a pair of CNN networks are used to measure similarity between two objects, and the CNNs are trained with loss functions that learn features that best differentiate them. 
             <p align="center">
            <img src="./media/figure_SiameseNetwork.jpg" width="400" align="center"/>
            </p>
<center>

 Source: [(Simon-Serra et al, 2015)](https://www.cv-foundation.org/openaccess/content_iccv_2015/papers/Simo-Serra_Discriminative_Learning_of_ICCV_2015_paper.pdf)

</center>

In an LSTM network, extracted features from different detections in different time frames are used as inputs. The network predicts the bounding box for the next frame based on the input history.
             <p align="center">
            <img src="./media/figure_LSTM.jpg" width="550" align="center"/>
            </p>
<center>

Source: [Ciaparrone, 2019](https://arxiv.org/pdf/1907.12740.pdf)

</center>

Correlation filters can also be convolved with feature maps from CNN network to generate a prediction of the target's location in the next time frame. This was done by [Ma et al](https://faculty.ucmerced.edu/mhyang/papers/iccv15_tracking.pdf) as follows:
            <p align="center">
            <img src="./media/figure_CNNcorrFilters.jpg" width="500" align="center"/>
            </p>


### What SoTA affinity and association techniques are used in tracking-by-detection trackers? 
Simple approaches use similarity/affinity scores calculated from distance measures over features extracted by the CNN to optimally match object detections/tracklets with established object tracks across successive frames. To do this matching, Hungarian (Huhn-Munkres) algorithm is often used for online data association, while K-partite graph global optimization techniques are used for offline data association. 

In more complex deep-learning approaches, the affinity computation is often merged with feature extraction. For instance, [Siamese CNNs](https://arxiv.org/pdf/1907.12740.pdf) and [Siamese LSTMs](http://openaccess.thecvf.com/content_cvpr_2018_workshops/papers/w21/Wan_An_Online_and_CVPR_2018_paper.pdf) directly output the affinity score.



### What is the difference between online and offline tracking algorithms? 
Online and offline algorithms differ at their data association step. In online tracking, the detections in a new frame are associated with tracks generated previously from previous frames. Thus, existing tracks are extended or new tracks are created. In offline (batch) tracking, all observations in a batch of frames are considered globally (see figure below), i.e. they are linked together into tracks by obtaining a global optimal solution. Offline tracking can perform better with tracking issues such as long-term occlusion, or similar targets that are spatially close. However, offline tracking is slow, hence not suitable for online tasks such as for autonomous driving. Recently, research has focused on online tracking algorithms, which have reached the performance of offlinetracking while still maintaining high inference speed.

<p align="center">
<img src="./media/fig_onlineBatch.jpg" width="400" align="center"/>
</p>


## Popular publications

| Name | Year | MOT16 IDF1 | MOT16 MOTA | Inference Speed(fps) | Online/ Batch | Detector |  Feature extraction/ motion model | Affinity & Association Approach |
| ---- | ---- | ---------- | ---------- | -------------------- | ------------- | -------- | -------------------------------- | -------------------- |
|[A Simple Baseline for Multi-object Tracking -FairMOT](https://arxiv.org/pdf/2004.01888.pdf)|2020|70.4|68.7|25.8|Online|One-shot tracker with detector head|One-shot tracker with re-id head & multi-layer feature aggregation, IOU, Kalman Filter| JV algorithm on IOU, embedding distance,
|[How to Train Your Deep Multi-Object Tracker -DeepMOT-Tracktor](https://arxiv.org/pdf/1906.06618v2.pdf)|2020|53.4|54.8|1.6|Online|Single object tracker: Faster-RCNN (Tracktor), GO-TURN, SiamRPN|Tracktor, CNN re-id module|Deep Hungarian Net using Bi-RNN|
|[Tracking without bells and whistles -Tracktor](https://arxiv.org/pdf/1903.05625.pdf)|2019|54.9|56.2|1.6|Online|Modified Faster-RCNN| Temporal bbox regression with bbox camera motion compensation, re-id embedding from Siamese CNN| Greedy heuristic to merge tracklets using re-id embedding distance|
|[Towards Real-Time Multi-Object Tracking -JDE](https://arxiv.org/pdf/1909.12605v1.pdf)|2019|55.8|64.4|18.5|Online|One-shot tracker - Faster R-CNN with FPN|One-shot - Faster R-CNN with FPN, Kalman Filter|Hungarian Algorithm|
|[Exploit the connectivity: Multi-object tracking with TrackletNet -TNT](https://arxiv.org/pdf/1811.07258.pdf)|2019|56.1|49.2|0.7|Batch|MOT challenge detections|CNN with bbox camera motion compensation, embedding feature similarity|CNN-based similarity measures between tracklet pairs; tracklet-based graph-cut optimization|
|[Extending IOU based Multi-Object Tracking by Visual Information -VIOU](http://elvera.nue.tu-berlin.de/typo3/files/1547Bochinski2018.pdf)|2018|56.1(VisDrone)|40.2(VisDrone)|20(VisDrone)|Batch|Mask R-CNN, CompACT|IOU|KCF to merge tracklets using greedy IOU heuristics|
|[Simple Online and Realtime Tracking with a Deep Association Metric -DeepSORT](https://arxiv.org/pdf/1703.07402v1.pdf)|2017|62.2| 61.4|17.4|Online|Modified Faster R-CNN|CNN re-id module, IOU, Kalman Filter|Hungarian Algorithm, cascaded approach using Mahalanobis distance (motion), embedding distance |
|[Multiple people tracking by lifted multicut and person re-identification -LMP](http://openaccess.thecvf.com/content_cvpr_2017/papers/Tang_Multiple_People_Tracking_CVPR_2017_paper.pdf)|2017|51.3|48.8|0.5|Batch|[Public detections](https://arxiv.org/pdf/1610.06136.pdf)|StackeNetPose CNN re-id module|Spatio-temporal relations, deep-matching, re-id confidence; detection-based graph lifted-multicut optimization|
