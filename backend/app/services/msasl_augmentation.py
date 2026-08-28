"""
Train-set-only data augmentation for the MS-ASL word-sign classifier
(train_msasl_classifier.py). Operates on the already body-normalized,
15-frame-resampled sequences produced by word_landmark_features, so it
works directly off msasl_intermediate_landmarks.csv without needing the
original video clips.

This exists because an experiment (see git history /
scripts/improve_msasl_classifier.py) found the real bottleneck for this
dataset wasn't the classifier — it was too few real clips per word (as
low as 5). Augmentation alone only moved test accuracy from 32.5% to
~34% (noise); the real fix was reducing the vocabulary to words with
enough real samples (see train_msasl_classifier.py). Augmentation is
still applied on top of that, for a modest additional boost — but it is
NEVER applied to val/test splits, only train, so reported accuracy
stays honest.
"""

import numpy as np

from app.services.word_landmark_features import (
    FIXED_FRAMES,
    HAND_LANDMARK_COUNT,
    LEFT_HAND_START,
    POSE_ORDER,
    RIGHT_HAND_START,
)

POSE_MIRROR_PAIRS = [
    (POSE_ORDER.index("left_shoulder"), POSE_ORDER.index("right_shoulder")),
    (POSE_ORDER.index("left_elbow"), POSE_ORDER.index("right_elbow")),
    (POSE_ORDER.index("left_wrist"), POSE_ORDER.index("right_wrist")),
]


def mirror(seq: np.ndarray) -> np.ndarray:
    """Flip left-right: negate x, and swap left/right hand + pose blocks."""
    out = seq.copy()
    out[:, :, 0] *= -1
    lh = out[:, LEFT_HAND_START:LEFT_HAND_START + HAND_LANDMARK_COUNT, :].copy()
    rh = out[:, RIGHT_HAND_START:RIGHT_HAND_START + HAND_LANDMARK_COUNT, :].copy()
    out[:, LEFT_HAND_START:LEFT_HAND_START + HAND_LANDMARK_COUNT, :] = rh
    out[:, RIGHT_HAND_START:RIGHT_HAND_START + HAND_LANDMARK_COUNT, :] = lh
    for li, ri in POSE_MIRROR_PAIRS:
        l, r = out[:, li, :].copy(), out[:, ri, :].copy()
        out[:, li, :], out[:, ri, :] = r, l
    return out


def jitter(seq: np.ndarray, sigma: float, rng: np.random.Generator) -> np.ndarray:
    noise = rng.normal(0, sigma, seq.shape)
    out = seq + noise
    zero_mask = (seq == 0.0).all(axis=-1, keepdims=True)
    return np.where(np.broadcast_to(zero_mask, out.shape), 0.0, out)


def time_warp(seq: np.ndarray, n_frames: int) -> np.ndarray:
    src_t = np.linspace(0, 1, FIXED_FRAMES)
    mid_t = np.linspace(0, 1, n_frames)
    dst_t = np.linspace(0, 1, FIXED_FRAMES)
    mid = np.empty((n_frames, seq.shape[1], seq.shape[2]))
    for p in range(seq.shape[1]):
        for a in range(seq.shape[2]):
            mid[:, p, a] = np.interp(mid_t, src_t, seq[:, p, a])
    out = np.empty_like(seq)
    for p in range(seq.shape[1]):
        for a in range(seq.shape[2]):
            out[:, p, a] = np.interp(dst_t, mid_t, mid[:, p, a])
    return out


def scale_jitter(seq: np.ndarray, factor: float) -> np.ndarray:
    out = seq.copy()
    out[:, :, :2] *= factor
    return out


def augment_dataset(
    seqs: np.ndarray, labels: np.ndarray, per_sample: int = 4, random_seed: int = 42
) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns (augmented_seqs, augmented_labels) — ORIGINALS NOT INCLUDED;
    caller concatenates with the real train data. Never call this on
    val/test data.
    """
    rng = np.random.default_rng(random_seed)
    aug_seqs, aug_labels = [], []
    for seq, label in zip(seqs, labels):
        variants = [
            mirror(seq),
            jitter(seq, sigma=0.015, rng=rng),
            time_warp(seq, int(rng.integers(10, 20))),
            scale_jitter(jitter(mirror(seq), sigma=0.01, rng=rng), float(rng.uniform(0.9, 1.1))),
            jitter(time_warp(seq, int(rng.integers(10, 20))), sigma=0.01, rng=rng),
        ]
        for v in variants[:per_sample]:
            aug_seqs.append(v)
            aug_labels.append(label)
    return np.array(aug_seqs), np.array(aug_labels)
