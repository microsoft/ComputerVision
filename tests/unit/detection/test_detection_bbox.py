# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from utils_cv.detection.bbox import DetectionBbox, AnnotationBbox, _Bbox


@pytest.fixture(scope="session")
def basic_bbox() -> "_Bbox":
    return _Bbox(left=0, top=10, right=100, bottom=1000)


@pytest.fixture(scope="session")
def anno_bbox() -> "AnnotationBbox":
    return AnnotationBbox(left=0, top=10, right=100, bottom=1000, label_idx=0)


@pytest.fixture(scope="session")
def det_bbox() -> "DetectionBbox":
    return DetectionBbox(
        left=0, top=10, right=100, bottom=1000, label_idx=0, score=0.5
    )


def validate_bbox(bbox: _Bbox) -> bool:
    assert bbox.left == 0
    assert bbox.top == 10
    assert bbox.right == 100
    assert bbox.bottom == 1000


def text__bbox_init(basic_bbox):
    assert type(basic_bbox) == _Bbox
    validate_bbox(basic_bbox)


def test__bbox_from_array(basic_bbox):
    # test `from_array()` bbox initialization method
    bbox_from_array = _Bbox.from_array([0, 10, 100, 1000])
    validate_bbox(bbox_from_array)
    # test `from_array_xymh()` bbox initialization method
    bbox_from_array_xywh = _Bbox.from_array_xywh([0, 10, 100, 990])
    validate_bbox(bbox_from_array_xywh)


def test__bbox_basic_funcs(basic_bbox):
    # test rect()
    assert basic_bbox.rect() == [0, 10, 100, 1000]
    # test width()
    assert basic_bbox.width() == 100
    # test height()
    assert basic_bbox.height() == 990
    # test surface_area()
    assert basic_bbox.surface_area() == 99000


def test__bbox_overlap(basic_bbox):
    # test bbox that does not overlap
    non_overlapping_bbox = _Bbox(left=200, top=10, right=300, bottom=1000)
    overlap = basic_bbox.get_overlap_bbox(non_overlapping_bbox)
    assert overlap is None
    # test bbox that does overlap
    overlapping_bbox = _Bbox(left=0, top=500, right=100, bottom=2000)
    overlap = basic_bbox.get_overlap_bbox(overlapping_bbox)
    assert overlap == _Bbox(left=0, top=500, right=100, bottom=1000)


def test__bbox_crop(basic_bbox):
    # test valid crop sizes
    cropped_bbox = basic_bbox.crop(max_width=10, max_height=10)
    assert cropped_bbox.width() == 10
    assert cropped_bbox.height() == 10
    assert cropped_bbox.left == 0
    assert cropped_bbox.top == 10
    assert cropped_bbox.right == 10
    assert cropped_bbox.bottom == 20
    # test invalid crop sizes
    with pytest.raises(Exception):
        basic_bbox.crap(max_width=101, max_height=10)


def test__bbox_standardization():
    non_standard_bbox_0 = _Bbox(left=100, top=1000, right=0, bottom=10)
    validate_bbox(non_standard_bbox_0)


def test__bbox_is_valid(basic_bbox):
    assert basic_bbox.is_valid() is True
    assert _Bbox(left=0, top=0, right=0, bottom=0).is_valid() is False


def test_annotation_bbox_init(anno_bbox):
    validate_bbox(anno_bbox)
    assert type(anno_bbox) == AnnotationBbox


def test_annotation_bbox_from_array(anno_bbox):
    bbox_from_array = AnnotationBbox.from_array(
        [0, 10, 100, 1000], label_idx=0
    )
    validate_bbox(bbox_from_array)
    assert type(bbox_from_array) == AnnotationBbox


def test_detection_bbox_init(det_bbox):
    validate_bbox(det_bbox)
    assert type(det_bbox) == DetectionBbox


def test_detection_bbox_from_array(det_bbox):
    bbox_from_array = DetectionBbox.from_array(
        [0, 10, 100, 1000], label_idx=0, score=0
    )
    validate_bbox(det_bbox)
    assert type(bbox_from_array) == DetectionBbox
