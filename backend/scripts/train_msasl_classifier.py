"""
Trains the Intermediate Conversational Fluency temporal sign classifier
on data/processed/msasl_intermediate_landmarks.csv (produced by
prepare_msasl_dataset.py), using MS-ASL's own train/val/test split
(assigned by the dataset's creators, not re-split here) — a more
rigorous held-out evaluation than a self-constructed split.

v2 (this file replaces the original all-30-words version): an honest
experiment (scripts/improve_msasl_classifier.py,
scripts/vocab_reduction_experiment.py) found that augmenting/re-featuring
the raw 30-word dataset barely moved test accuracy (32.5% -> ~34%,
within noise) because several words only had 5-9 real clips. What
actually helped was restricting the vocabulary to words with enough
real samples per class — the model was never the bottleneck, sample
count was. So this script:

  1. Drops any word with fewer than MIN_SAMPLES_PER_CLASS total real
     clips (train+val+test combined) — MIN_SAMPLES_PER_CLASS=15 keeps
     16 of the original 30 words and got 49% test accuracy in the
     experiment, vs. 32.5% keeping all 30.
  2. Augments the (real-only) train split with mirroring, Gaussian
     jitter, time-warp and scale-jitter (train_msasl_augmentation.py) —
     val/test are NEVER augmented, so the reported accuracy is exactly
     as honest as the original script's.
  3. Picks feature representation + classifier by val accuracy only
     (never by test), then reports test accuracy once, on the untouched
     real test split, with that chosen config refit on train+val.

--course selects which prepared feature CSV to train on (matches
prepare_msasl_dataset.py's --course) — defaults to "intermediate" so
the original one-course invocation still works unchanged. The model
file, confusion matrix, and vocabulary_source metadata are all named
after the chosen course, so intermediate and professional models never
collide on disk.

Run from backend/:
    python3 scripts/train_msasl_classifier.py
    python3 scripts/train_msasl_classifier.py --course professional
"""

import argparse
import csv
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from app.services.msasl_augmentation import augment_dataset
from app.services.word_landmark_features import (
    FIXED_FRAMES,
    HAND_LANDMARK_COUNT,
    POSE_ORDER,
    flatten_features,
    pooled_features,
)

BACKEND_ROOT = Path(__file__).resolve().parent.parent

RANDOM_SEED = 42
MIN_SAMPLES_PER_CLASS = 15
POINTS_PER_FRAME = len(POSE_ORDER) + HAND_LANDMARK_COUNT * 2


def load_dataset(features_csv: Path):
    with open(features_csv, newline="") as f:
        reader = csv.reader(f)
        next(reader)
        rows = list(reader)
    labels = np.array([row[0] for row in rows])
    splits = np.array([row[1] for row in rows])
    flat = np.array([[float(v) for v in row[4:]] for row in rows])
    seqs = flat.reshape(len(rows), FIXED_FRAMES, POINTS_PER_FRAME, 3)
    return seqs, labels, splits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--course", default="intermediate",
        help="Which prepared feature CSV to train on (matches prepare_msasl_dataset.py's --course). "
             "Default: intermediate. Use 'professional' for Workplace Communication.",
    )
    args = parser.parse_args()
    course = args.course

    features_csv = BACKEND_ROOT / "data" / "processed" / f"msasl_{course}_landmarks.csv"
    model_path = BACKEND_ROOT / "data" / "models" / f"msasl_{course}_classifier.pkl"
    confusion_matrix_png = BACKEND_ROOT / "data" / "processed" / f"msasl_{course}_confusion_matrix.png"

    if not features_csv.exists():
        raise FileNotFoundError(f"Feature CSV not found: {features_csv}. Run prepare_msasl_dataset.py first.")

    seqs, labels, splits = load_dataset(features_csv)
    all_classes = sorted(set(labels))
    print(f"Loaded {len(labels)} real samples across {len(all_classes)} words")

    from collections import Counter
    counts = Counter(labels)
    keep = {w for w, n in counts.items() if n >= MIN_SAMPLES_PER_CLASS}
    dropped = sorted(set(all_classes) - keep)
    print(f"Keeping {len(keep)} words with >= {MIN_SAMPLES_PER_CLASS} real samples each")
    print(f"Dropped for insufficient data (<{MIN_SAMPLES_PER_CLASS} samples): {dropped}")

    mask = np.isin(labels, list(keep))
    seqs, labels, splits = seqs[mask], labels[mask], splits[mask]
    classes = sorted(keep)

    seq_train, y_train = seqs[splits == "train"], labels[splits == "train"]
    seq_val, y_val = seqs[splits == "val"], labels[splits == "val"]
    seq_test, y_test = seqs[splits == "test"], labels[splits == "test"]
    print(f"  train: {len(y_train)}  val: {len(y_val)}  test: {len(y_test)}")

    aug_seq, aug_labels = augment_dataset(seq_train, y_train, per_sample=4, random_seed=RANDOM_SEED)
    seq_train_aug = np.concatenate([seq_train, aug_seq], axis=0)
    y_train_aug = np.concatenate([y_train, aug_labels], axis=0)
    print(f"  train after augmentation: {len(y_train_aug)} ({len(aug_labels)} synthetic + {len(y_train)} real)")

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
            ("svc", SVC(kernel="rbf", C=8, gamma="scale", probability=True, random_state=RANDOM_SEED)),
        ]),
        "LogReg": lambda: Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=3000, C=1.0, random_state=RANDOM_SEED)),
        ]),
    }
    train_variants = {"no_aug": (seq_train, y_train), "with_aug": (seq_train_aug, y_train_aug)}

    results = []
    for fname, fbuild in feature_builders.items():
        Xval = fbuild(seq_val)
        for tname, (seq_t, y_t) in train_variants.items():
            Xtrain = fbuild(seq_t)
            for cname, cbuild in classifiers.items():
                model = cbuild()
                model.fit(Xtrain, y_t)
                val_acc = accuracy_score(y_val, model.predict(Xval))
                results.append((fname, tname, cname, val_acc))
                print(f"[{fname:12s} | {tname:9s} | {cname:16s}] val acc = {val_acc:.4f}")

    results.sort(key=lambda r: r[3], reverse=True)
    best_fname, best_tname, best_cname, best_val_acc = results[0]
    print(f"\nBest config on val: features={best_fname}, train={best_tname}, model={best_cname} (val acc {best_val_acc:.4f})")

    fbuild = feature_builders[best_fname]
    seq_t, y_t = train_variants[best_tname]
    seq_trainval = np.concatenate([seq_t, seq_val], axis=0)
    y_trainval = np.concatenate([y_t, y_val], axis=0)

    final_model = classifiers[best_cname]()
    final_model.fit(fbuild(seq_trainval), y_trainval)

    Xtest = fbuild(seq_test)
    test_preds = final_model.predict(Xtest)
    test_acc = accuracy_score(y_test, test_preds)
    print(f"\n=== Final test accuracy ({best_cname}, {best_fname}, {best_tname}): {test_acc:.4f} (n={len(y_test)}) ===\n")
    print(classification_report(y_test, test_preds, labels=classes, zero_division=0))

    cm = confusion_matrix(y_test, test_preds, labels=classes)
    print("=== Confusion matrix on TEST split (rows = true label, columns = predicted) ===")
    print("           " + " ".join(f"{label[:9]:>9}" for label in classes))
    for label, row in zip(classes, cm):
        print(f"{label[:10]:>10} " + " ".join(f"{v:>9}" for v in row))

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": final_model,
            "classes": classes,
            "model_name": best_cname,
            "feature_set": best_fname,
            "fixed_frames": FIXED_FRAMES,
            "vocabulary_source": f"MS-ASL {course} curriculum (C-UDA 0.1 licensed, research/computational use only)",
            "test_accuracy": test_acc,
            "min_samples_per_class": MIN_SAMPLES_PER_CLASS,
            "dropped_for_insufficient_data": dropped,
            "trained_with_augmentation": best_tname == "with_aug",
        },
        model_path,
    )
    print(f"\nSaved model to: {model_path}")

    fig, ax = plt.subplots(figsize=(9, 9))
    ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classes).plot(
        ax=ax, xticks_rotation="vertical", colorbar=False
    )
    ax.set_title(f"{best_cname} test-split confusion matrix (accuracy {test_acc:.2%}, {len(classes)} words)")
    fig.tight_layout()
    fig.savefig(confusion_matrix_png, dpi=150)
    print(f"Saved confusion matrix plot to: {confusion_matrix_png}")


if __name__ == "__main__":
    main()
