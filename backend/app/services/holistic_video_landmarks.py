"""
Extracts per-frame pose + both-hand landmarks from a short video clip
using MediaPipe Tasks (PoseLandmarker + HandLandmarker), producing the
same (n_frames, 49, 3) raw sequence array shape that
word_landmark_features.extract_raw_sequence produces from the Kaggle
parquet files — so normalize_sequence/resample_sequence downstream are
shared, unmodified, between the Kaggle-subset pipeline and this
MS-ASL-video pipeline. Point order matches
word_landmark_features.POSE_ORDER exactly: 7 pose points, then 21
left-hand points, then 21 right-hand points.
"""

from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    PoseLandmarker,
    PoseLandmarkerOptions,
    RunningMode,
)

from app.services.word_landmark_features import (
    HAND_LANDMARK_COUNT,
    LEFT_HAND_START,
    POINTS_PER_FRAME,
    POSE_LANDMARKS,
    POSE_ORDER,
    RIGHT_HAND_START,
)

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "models"
HAND_MODEL_PATH = MODELS_DIR / "hand_landmarker.task"
POSE_MODEL_PATH = MODELS_DIR / "pose_landmarker.task"

_hand_landmarker: HandLandmarker | None = None
_pose_landmarker: PoseLandmarker | None = None


def _get_hand_landmarker() -> HandLandmarker:
    global _hand_landmarker
    if _hand_landmarker is None:
        if not HAND_MODEL_PATH.exists():
            raise FileNotFoundError(f"Hand landmarker model not found: {HAND_MODEL_PATH}")
        _hand_landmarker = HandLandmarker.create_from_options(HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(HAND_MODEL_PATH)),
            running_mode=RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.5,
        ))
    return _hand_landmarker


def _get_pose_landmarker() -> PoseLandmarker:
    global _pose_landmarker
    if _pose_landmarker is None:
        if not POSE_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Pose landmarker model not found: {POSE_MODEL_PATH}. "
                "Download a pose_landmarker*.task file from the MediaPipe Tasks model zoo first."
            )
        _pose_landmarker = PoseLandmarker.create_from_options(PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(POSE_MODEL_PATH)),
            running_mode=RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
        ))
    return _pose_landmarker


def extract_raw_sequence_from_video(video_path: str, frame_stride: int = 1) -> np.ndarray:
    """
    Reads every `frame_stride`-th frame of video_path, runs pose + both-
    hand detection on each, and returns a (n_frames, 49, 3) array in the
    same point order as word_landmark_features.extract_raw_sequence
    (pose points in POSE_ORDER, then 21 left-hand, then 21 right-hand
    points). Missing detections are NaN, handled downstream by
    normalize_sequence exactly like the Kaggle-parquet path — so this
    and extract_raw_sequence are interchangeable inputs to the same
    normalize_sequence/resample_sequence pipeline.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")

    hand_landmarker = _get_hand_landmarker()
    pose_landmarker = _get_pose_landmarker()

    frames_out = []
    try:
        frame_idx = 0
        while True:
            ok, image = cap.read()
            if not ok:
                break
            if frame_idx % frame_stride != 0:
                frame_idx += 1
                continue

            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

            point_row = np.full((POINTS_PER_FRAME, 3), np.nan, dtype=np.float64)

            pose_result = pose_landmarker.detect(mp_image)
            if pose_result.pose_landmarks:
                landmarks = pose_result.pose_landmarks[0]
                for pi, name in enumerate(POSE_ORDER):
                    lm = landmarks[POSE_LANDMARKS[name]]
                    point_row[pi] = (lm.x, lm.y, lm.z)

            hand_result = hand_landmarker.detect(mp_image)
            for hand_landmarks, handedness in zip(hand_result.hand_landmarks, hand_result.handedness):
                # MediaPipe's own Left/Right convention — kept consistent with
                # how the Kaggle dataset's left_hand/right_hand columns were
                # produced, since both come from the same underlying model family.
                label = handedness[0].category_name
                start = LEFT_HAND_START if label == "Left" else RIGHT_HAND_START
                for hi in range(HAND_LANDMARK_COUNT):
                    lm = hand_landmarks[hi]
                    point_row[start + hi] = (lm.x, lm.y, lm.z)

            frames_out.append(point_row)
            frame_idx += 1
    finally:
        cap.release()

    if not frames_out:
        return np.empty((0, POINTS_PER_FRAME, 3), dtype=np.float64)
    return np.stack(frames_out, axis=0)
