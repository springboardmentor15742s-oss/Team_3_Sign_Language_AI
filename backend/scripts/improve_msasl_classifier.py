"""
Attempt to improve on the 32.5% test accuracy of the Intermediate
Conversational Fluency classifier (train_msasl_classifier.py), WITHOUT
collecting any new video clips (none are available in this
environment). Two honest, data-available levers are tried:

  1. Train-set-only augmentation (mirroring, Gaussian jitter, temporal
     time-warp, scale jitter) applied to the *already-extracted*
     normalized landmark sequences reconstructed from
     msasl_intermediate_landmarks.csv. Val/test are NEVER augmented —
     augmenting eval data would inflate the reported number
     dishonestly.
  2. A more compact, less overfit-prone feature representation
     (per-landmark mean/std/min/max/range pooled over the 15 frames,
     441 dims) tried alongside the original raw flatten (2205 dims),
     since 2205 raw features vs. 326 train rows is a bad
     samples-to-dimensions ratio regardless of classifier.

Model selection (which feature set + which classifier + how much
augmentation) is done ENTIRELY on the val split, exactly like the
original script. Test accuracy is computed once, at the end, on the
untouched test split with the config chosen by val — never used to
pick the config itself.

Run from backend/:
    python3 scripts/improve_msasl_classifier.py
"""

import csv
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from app.services.word_landmark_features import (
    AXES,
    FIXED_FRAMES,
    HAND_LANDMARK_COUNT,
    LEFT_HAND_START,
    POSE_ORDER,
    RIGHT_HAND_START,
)

BACKEND_ROOT = Path(__file__).resolve().parent.parent
COURSE = "intermediate"
FEATURES_CSV = BACKEND_ROOT / "data" / "processed" / f"msasl_{COURSE}_landmarks.csv"
MODEL_PATH = BACKEND_ROOT / "data" / "models" / f"msasl_{COURSE}_classifier.pkl"

RANDOM_SEED = 42
POINTS_PER_FRAME = len(POSE_ORDER) + HAND_LANDMARK_COUNT * 2  # 49
N_AXES = len(AXES)  # 3

# --- left/right pose landmark pairing, for mirror augmentation ---
POSE_MIRROR_PAIRS = [
    (POSE_ORDER.index("left_shoulder"), POSE_ORDER.index("right_shoulder")),
    (POSE_ORDER.index("left_elbow"), POSE_ORDER.index("right_elbow")),
    (POSE_ORDER.index("left_wrist"), POSE_ORDER.index("right_wrist")),
]


def load_dataset():
    with open(FEATURES_CSV, newline="") as f:
        reader = csv.reader(f)
        next(reader)
        rows = list(reader)
    labels = np.array([row[0] for row in rows])
    splits = np.array([row[1] for row in rows])
    flat = np.array([[float(v) for v in row[4:]] for row in rows])
    seqs = flat.reshape(len(rows), FIXED_FRAMES, POINTS_PER_FRAME, N_AXES)
    return seqs, labels, splits


# ---------------------------------------------------------------- augmentation
rng = np.random.default_rng(RANDOM_SEED)


def mirror(seq: np.ndarray) -> np.ndarray:
    """Flip left-right: negate x, and swap left/right hand + pose blocks."""
    out = seq.copy()
    out[:, :, 0] *= -1  # negate x for every point (body-centered origin)

    # swap the two hand blocks entirely (mirrored signer's "dominant"
    # hand identity flips)
    left_hand = out[:, LEFT_HAND_START:LEFT_HAND_START + HAND_LANDMARK_COUNT, :].copy()
    right_hand = out[:, RIGHT_HAND_START:RIGHT_HAND_START + HAND_LANDMARK_COUNT, :].copy()
    out[:, LEFT_HAND_START:LEFT_HAND_START + HAND_LANDMARK_COUNT, :] = right_hand
    out[:, RIGHT_HAND_START:RIGHT_HAND_START + HAND_LANDMARK_COUNT, :] = left_hand

    for li, ri in POSE_MIRROR_PAIRS:
        l = out[:, li, :].copy()
        r = out[:, ri, :].copy()
        out[:, li, :] = r
        out[:, ri, :] = l
    return out


def jitter(seq: np.ndarray, sigma: float = 0.015) -> np.ndarray:
    noise = rng.normal(0, sigma, seq.shape)
    out = seq + noise
    # keep exact-zero "hand not detected" blocks exactly zero, don't invent a hand
    zero_mask = (seq == 0.0).all(axis=-1, keepdims=True)
    out = np.where(np.broadcast_to(zero_mask, out.shape), 0.0, out)
    return out


def time_warp(seq: np.ndarray, n_frames: int) -> np.ndarray:
    """Resample to n_frames then back to FIXED_FRAMES, changing effective speed."""
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
    out[:, :, :2] *= factor  # x,y only; z left alone (already scale-normalized separately)
    return out


def augment_dataset(seqs: np.ndarray, labels: np.ndarray, per_sample: int) -> tuple[np.ndarray, np.ndarray]:
    """Returns (augmented_seqs, augmented_labels) — ORIGINALS NOT INCLUDED,
    caller concatenates with the real data."""
    aug_seqs, aug_labels = [], []
    for seq, label in zip(seqs, labels):
        variants = []
        variants.append(mirror(seq))
        variants.append(jitter(seq))
        variants.append(time_warp(seq, int(rng.integers(10, 20))))
        variants.append(scale_jitter(jitter(mirror(seq), sigma=0.01), float(rng.uniform(0.9, 1.1))))
        variants.append(jitter(time_warp(seq, int(rng.integers(10, 20))), sigma=0.01))
        for v in variants[:per_sample]:
            aug_seqs.append(v)
            aug_labels.append(label)
    return np.array(aug_seqs), np.array(aug_labels)


# ---------------------------------------------------------------- feature sets
def flatten_features(seqs: np.ndarray) -> np.ndarray:
    return seqs.reshape(len(seqs), -1)


def pooled_features(seqs: np.ndarray) -> np.ndarray:
    """Per (point, axis) mean/std/min/max/range across the 15 frames -> 49*3*5=735 dims,
    plus simple motion-energy features (mean abs frame-to-frame delta per point)."""
    mean = seqs.mean(axis=1)
    std = seqs.std(axis=1)
    mn = seqs.min(axis=1)
    mx = seqs.max(axis=1)
    rng_ = mx - mn
    deltas = np.diff(seqs, axis=1)
    motion = np.abs(deltas).mean(axis=1)  # (n, points, axes)
    pooled = np.concatenate(
        [mean, std, mn, mx, rng_, motion], axis=2
    )  # concat along axis dim -> (n, points, axes*6)
    return pooled.reshape(len(seqs), -1)


def main():
    seqs, labels, splits = load_dataset()
    classes = sorted(set(labels))
    print(f"Loaded {len(labels)} real samples across {len(classes)} classes")

    train_mask, val_mask, test_mask = splits == "train", splits == "val", splits == "test"
    seq_train, y_train_real = seqs[train_mask], labels[train_mask]
    seq_val, y_val = seqs[val_mask], labels[val_mask]
    seq_test, y_test = seqs[test_mask], labels[test_mask]
    print(f"  train: {len(y_train_real)}  val: {len(y_val)}  test: {len(y_test)}")

    aug_seq, aug_labels = augment_dataset(seq_train, y_train_real, per_sample=4)
    seq_train_aug = np.concatenate([seq_train, aug_seq], axis=0)
    y_train_aug = np.concatenate([y_train_real, aug_labels], axis=0)
    print(f"  train after augmentation: {len(y_train_aug)} ({len(aug_labels)} synthetic + {len(y_train_real)} real)", flush=True)

    feature_builders = {"raw_flatten": flatten_features, "pooled_stats": pooled_features}

    classifiers = {
        "RandomForest": lambda: RandomForestClassifier(
            n_estimators=400, max_depth=18, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1
        ),
        "HistGradBoosting": lambda: HistGradientBoostingClassifier(
            max_iter=150, max_depth=4, learning_rate=0.1, random_state=RANDOM_SEED
        ),
        "SVM_rbf": lambda: Pipeline([
            ("scaler", StandardScaler()),
            ("svc", SVC(kernel="rbf", C=8, gamma="scale", probability=False, random_state=RANDOM_SEED)),
        ]),
        "LogReg": lambda: Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=3000, C=1.0, random_state=RANDOM_SEED)),
        ]),
    }

    train_variants = {
        "no_aug": (seq_train, y_train_real),
        "with_aug": (seq_train_aug, y_train_aug),
    }

    results = []
    for fname, fbuild in feature_builders.items():
        Xval = fbuild(seq_val)
        for tname, (seq_t, y_t) in train_variants.items():
            Xtrain = fbuild(seq_t)
            for cname, cbuild in classifiers.items():
                t0 = time.time()
                model = cbuild()
                model.fit(Xtrain, y_t)
                val_preds = model.predict(Xval)
                val_acc = accuracy_score(y_val, val_preds)
                results.append((fname, tname, cname, val_acc, model))
                print(f"[{fname:12s} | {tname:9s} | {cname:16s}] val acc = {val_acc:.4f}  ({time.time()-t0:.1f}s)", flush=True)

    results.sort(key=lambda r: r[3], reverse=True)
    best_fname, best_tname, best_cname, best_val_acc, _ = results[0]
    print(f"\nBest config on val: features={best_fname}, train={best_tname}, model={best_cname} "
          f"(val acc {best_val_acc:.4f})")

    # Refit the winning config on train+val combined (still never touching
    # test), same spirit as the original script picking on val then
    # reporting test once.
    fbuild = feature_builders[best_fname]
    seq_t, y_t = train_variants[best_tname]
    seq_trainval = np.concatenate([seq_t, seq_val], axis=0)
    y_trainval = np.concatenate([y_t, y_val], axis=0)
    final_model = classifiers[best_cname]()
    final_model.fit(fbuild(seq_trainval), y_trainval)

    Xtest = fbuild(seq_test)
    test_preds = final_model.predict(Xtest)
    test_acc = accuracy_score(y_test, test_preds)
    print(f"\n=== FINAL test accuracy (chosen-by-val config, refit on train+val): {test_acc:.4f} (n={len(y_test)}) ===\n")
    print(classification_report(y_test, test_preds, labels=classes, zero_division=0))

    # Also report what the OLD baseline (raw_flatten, no_aug, best of RF/SVM
    # picked by val among just those two) would get on this same test set,
    # for a fair side-by-side.
    baseline_candidates = [r for r in results if r[0] == "raw_flatten" and r[1] == "no_aug" and r[2] in ("RandomForest", "SVM_rbf")]
    baseline_best = max(baseline_candidates, key=lambda r: r[3])
    baseline_model = classifiers[baseline_best[2]]()
    baseline_model.fit(flatten_features(seq_train), y_train_real)
    baseline_test_acc = accuracy_score(y_test, baseline_model.predict(flatten_features(seq_test)))
    print(f"(For comparison: original raw_flatten/no_aug/{baseline_best[2]} baseline test acc = {baseline_test_acc:.4f})")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": final_model,
            "classes": classes,
            "model_name": best_cname,
            "feature_set": best_fname,
            "fixed_frames": FIXED_FRAMES,
            "vocabulary_source": "MS-ASL intermediate curriculum (C-UDA 0.1 licensed, research/computational use only)",
            "test_accuracy": test_acc,
            "trained_with_augmentation": best_tname == "with_aug",
        },
        MODEL_PATH,
    )
    print(f"\nSaved improved model to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
