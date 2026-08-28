"""
Shared feature extraction for the word-level (Kaggle ASL-signs subset)
temporal sign classifier. Used identically by prepare_word_dataset.py
(training) and, later, by the inference service, so features never
drift between the two — same discipline as
hand_tracking_service.normalize_landmarks for the static handshape
classifiers.

Unlike the static alphabet/common-signs classifiers (which normalize
each hand relative to its own wrist, deliberately discarding where in
frame the hand sits, since handshape alone is what matters there), word
signs often depend on WHERE the hand is relative to the body — e.g.
signs made near the chin/chest vs. out in front. So here every point in
a frame (both hands + a handful of pose landmarks) is normalized
relative to a shared body reference (the shoulder midpoint), scaled by
shoulder width, so hand position relative to the body is preserved
while the whole frame stays translation/scale invariant.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# MediaPipe Holistic pose landmark indices we keep as body-reference /
# arm-context points (33 total pose landmarks exist; we don't need all
# of them for isolated word signs).
POSE_LANDMARKS = {
    "nose": 0,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
}
POSE_ORDER = ["nose", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist"]

HAND_LANDMARK_COUNT = 21
FIXED_FRAMES = 15  # every sequence is resampled to this many frames, regardless of its original length
AXES = ("x", "y", "z")

# 7 pose points + 21 left-hand + 21 right-hand = 49 points x 3 axes = 147 features/frame
POINTS_PER_FRAME = len(POSE_ORDER) + HAND_LANDMARK_COUNT * 2
FEATURES_PER_FRAME = POINTS_PER_FRAME * len(AXES)

LEFT_SHOULDER_IDX = POSE_ORDER.index("left_shoulder")
RIGHT_SHOULDER_IDX = POSE_ORDER.index("right_shoulder")
LEFT_HAND_START = len(POSE_ORDER)
RIGHT_HAND_START = len(POSE_ORDER) + HAND_LANDMARK_COUNT


def _frame_points(frame_df: pd.DataFrame, type_name: str, index: int) -> tuple[float, float, float]:
    row = frame_df[(frame_df["type"] == type_name) & (frame_df["landmark_index"] == index)]
    if row.empty:
        return (np.nan, np.nan, np.nan)
    r = row.iloc[0]
    return (float(r["x"]), float(r["y"]), float(r["z"]))


def extract_raw_sequence(df: pd.DataFrame) -> np.ndarray:
    """
    Converts one parquet file's long-format landmark rows into a
    (n_frames, 49, 3) array in a fixed point order: pose points (in
    POSE_ORDER), then all 21 left-hand points, then all 21 right-hand
    points. Missing points (hand not detected that frame, or a pose
    point MediaPipe didn't find) are NaN, handled by normalize_sequence.
    """
    frames = sorted(df["frame"].unique())
    seq = np.full((len(frames), POINTS_PER_FRAME, 3), np.nan, dtype=np.float64)

    for fi, frame in enumerate(frames):
        frame_df = df[df["frame"] == frame]

        for pi, name in enumerate(POSE_ORDER):
            seq[fi, pi] = _frame_points(frame_df, "pose", POSE_LANDMARKS[name])

        for hi in range(HAND_LANDMARK_COUNT):
            seq[fi, len(POSE_ORDER) + hi] = _frame_points(frame_df, "left_hand", hi)
        for hi in range(HAND_LANDMARK_COUNT):
            seq[fi, len(POSE_ORDER) + HAND_LANDMARK_COUNT + hi] = _frame_points(frame_df, "right_hand", hi)

    return seq


def normalize_sequence(seq: np.ndarray) -> np.ndarray | None:
    """
    Per-frame: translate every point so the shoulder midpoint is the
    origin, and scale by shoulder width, so hand position relative to
    the body survives (unlike the static per-hand normalization) while
    the sequence stays invariant to where the signer stands in frame
    and how close they are to the camera.

    Frames where both shoulders are missing borrow the nearest frame's
    origin/scale (forward- then backward-fill) since MediaPipe pose
    tracking is usually stable within one short clip. Returns None if
    shoulders are missing in EVERY frame (nothing to anchor to).
    """
    left_sh = seq[:, LEFT_SHOULDER_IDX, :2]
    right_sh = seq[:, RIGHT_SHOULDER_IDX, :2]
    origin = (left_sh + right_sh) / 2.0
    scale = np.linalg.norm(left_sh - right_sh, axis=1)

    origin_df = pd.DataFrame(origin, columns=["ox", "oy"]).ffill().bfill()
    scale_series = pd.Series(scale).ffill().bfill()

    if origin_df.isna().any().any() or scale_series.isna().any():
        return None  # shoulders never detected in this sequence at all

    scale_series = scale_series.clip(lower=1e-4)

    normalized = seq.copy()
    for axis in range(2):  # normalize x, y against the body frame; leave z scaled but not re-centered
        col = "ox" if axis == 0 else "oy"
        normalized[:, :, axis] = (
            seq[:, :, axis] - origin_df[col].to_numpy()[:, None]
        ) / scale_series.to_numpy()[:, None]
    normalized[:, :, 2] = seq[:, :, 2] / scale_series.to_numpy()[:, None]

    # A hand missing in a given frame (not detected) becomes 0s for that
    # hand's block in that frame, rather than NaN, so it's a valid
    # "hand not present" signal the classifier can learn from instead
    # of a training-time crash.
    for start in (LEFT_HAND_START, RIGHT_HAND_START):
        block = normalized[:, start:start + HAND_LANDMARK_COUNT, :]
        missing_frame = np.isnan(block).any(axis=(1, 2))
        block[missing_frame] = 0.0
        normalized[:, start:start + HAND_LANDMARK_COUNT, :] = block

    # Any remaining NaNs (a stray missing pose point other than the
    # shoulders) get zero-filled too, same reasoning.
    normalized = np.nan_to_num(normalized, nan=0.0)
    return normalized


def resample_sequence(normalized: np.ndarray, fixed_frames: int = FIXED_FRAMES) -> np.ndarray:
    """
    Linearly interpolates every (point, axis) time series from however
    many frames the clip had to exactly `fixed_frames`, so sequences of
    different original lengths become directly comparable feature
    vectors.
    """
    n_frames = normalized.shape[0]
    if n_frames == 1:
        return np.repeat(normalized, fixed_frames, axis=0)

    src_t = np.linspace(0, 1, n_frames)
    dst_t = np.linspace(0, 1, fixed_frames)

    out = np.empty((fixed_frames, normalized.shape[1], normalized.shape[2]), dtype=np.float64)
    for p in range(normalized.shape[1]):
        for a in range(normalized.shape[2]):
            out[:, p, a] = np.interp(dst_t, src_t, normalized[:, p, a])
    return out


def extract_sequence_features(parquet_path: str, fixed_frames: int = FIXED_FRAMES) -> list[float] | None:
    """
    Full pipeline for one landmark parquet file: raw sequence -> body-
    relative normalization -> resample to fixed_frames -> flatten.
    Returns None if the sequence couldn't be normalized (no pose
    detected at all), so the caller can skip and log it.
    """
    df = pd.read_parquet(parquet_path)
    raw = extract_raw_sequence(df)
    normalized = normalize_sequence(raw)
    if normalized is None:
        return None
    resampled = resample_sequence(normalized, fixed_frames)
    return resampled.flatten().tolist()


def feature_column_names(fixed_frames: int = FIXED_FRAMES) -> list[str]:
    names = []
    for f in range(fixed_frames):
        for p in POSE_ORDER:
            for a in AXES:
                names.append(f"f{f}_pose_{p}_{a}")
        for hi in range(HAND_LANDMARK_COUNT):
            for a in AXES:
                names.append(f"f{f}_lhand{hi}_{a}")
        for hi in range(HAND_LANDMARK_COUNT):
            for a in AXES:
                names.append(f"f{f}_rhand{hi}_{a}")
    return names


# --- classifier input feature sets, shared between training
# (train_msasl_classifier.py) and live inference (word_sign_service.py)
# so a model trained on one representation is never fed the other.
# seqs here is a batch of already-normalized, already-resampled
# sequences: shape (n_samples, FIXED_FRAMES, POINTS_PER_FRAME, 3).

def flatten_features(seqs: np.ndarray) -> np.ndarray:
    """The original representation: every (frame, point, axis) value,
    flattened. High-dimensional (FIXED_FRAMES * POINTS_PER_FRAME * 3 =
    2205 at the defaults) relative to this project's small real sample
    counts, but keeps full temporal detail."""
    return seqs.reshape(len(seqs), -1)


def pooled_features(seqs: np.ndarray) -> np.ndarray:
    """A more compact representation: per (point, axis) mean/std/min/max/
    range across the FIXED_FRAMES frames, plus mean-abs frame-to-frame
    delta (a simple motion-energy signal) — 6 stats x POINTS_PER_FRAME x
    3 axes. Trades away exact temporal ordering for far fewer dimensions
    per sample, which matters more when real training samples are scarce."""
    mean = seqs.mean(axis=1)
    std = seqs.std(axis=1)
    mn = seqs.min(axis=1)
    mx = seqs.max(axis=1)
    value_range = mx - mn
    motion = np.abs(np.diff(seqs, axis=1)).mean(axis=1)
    pooled = np.concatenate([mean, std, mn, mx, value_range, motion], axis=2)
    return pooled.reshape(len(seqs), -1)


FEATURE_BUILDERS = {"raw_flatten": flatten_features, "pooled_stats": pooled_features}
