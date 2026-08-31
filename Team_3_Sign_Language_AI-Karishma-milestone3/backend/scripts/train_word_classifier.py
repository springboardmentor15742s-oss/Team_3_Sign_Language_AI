"""
Trains a word-level temporal sign classifier on the body-relative,
fixed-length trajectory features in data/processed/word_landmarks.csv
(produced by prepare_word_dataset.py), compares RandomForest vs SVM on
a held-out test split, and saves the better-performing model to
data/models/word_classifier.pkl.

Splits by participant_id (GroupShuffleSplit) rather than a plain random
split, so the same signer's movement style never appears in both train
and test — a plain stratified split would let the model partly
memorize a signer's idiosyncratic motion rather than genuinely
generalizing to a new person, and would over-report accuracy.

This is a proof-of-concept vocabulary (18 everyday Kaggle words) used
to validate this pipeline before running it on the real MS-ASL
curriculum data for the actual Intermediate/Professional course
content — see backend/data/curriculum/README.md. This model is not
wired into any API endpoint or the Courses page yet.

Run from backend/:
    venv/bin/python scripts/train_word_classifier.py
"""

import csv
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from app.services.word_landmark_features import FIXED_FRAMES

BACKEND_ROOT = Path(__file__).resolve().parent.parent
FEATURES_CSV = BACKEND_ROOT / "data" / "processed" / "word_landmarks.csv"
MODEL_PATH = BACKEND_ROOT / "data" / "models" / "word_classifier.pkl"
CONFUSION_MATRIX_PNG = BACKEND_ROOT / "data" / "processed" / "word_confusion_matrix.png"

TEST_SIZE = 0.2
RANDOM_SEED = 42


def load_dataset():
    with open(FEATURES_CSV, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # header
        rows = list(reader)

    labels = np.array([row[0] for row in rows])
    groups = np.array([row[1] for row in rows])
    features = np.array([[float(v) for v in row[3:]] for row in rows])
    return features, labels, groups


def group_aware_split(X, y, groups):
    """
    Falls back to a plain stratified split (with a printed warning) if
    the group split would leave any class entirely out of the test set
    — small classes (50 samples here) can lose all their held-out
    examples to one signer under GroupShuffleSplit by chance.
    """
    splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_SEED)
    train_idx, test_idx = next(splitter.split(X, y, groups))

    if set(y[train_idx]) == set(y[test_idx]) == set(y):
        print(
            f"Group-aware split by participant_id: {len(set(groups[train_idx]))} train signers, "
            f"{len(set(groups[test_idx]))} test signers (no signer overlap)"
        )
        return X[train_idx], X[test_idx], y[train_idx], y[test_idx]

    print(
        "WARNING: participant-based split left at least one class out of train or test — "
        "falling back to a stratified random split (less strict, but keeps every class evaluable)."
    )
    return train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y)


def main():
    if not FEATURES_CSV.exists():
        raise FileNotFoundError(f"Feature CSV not found: {FEATURES_CSV}. Run prepare_word_dataset.py first.")

    X, y, groups = load_dataset()
    classes = sorted(set(y))
    print(f"Loaded {len(y)} samples across {len(classes)} classes, {len(set(groups))} distinct signers")

    X_train, X_test, y_train, y_test = group_aware_split(X, y, groups)
    print(f"Train: {len(y_train)} samples, Test: {len(y_test)} samples\n")

    candidates = {
        "RandomForest": RandomForestClassifier(n_estimators=300, random_state=RANDOM_SEED, n_jobs=-1),
        "SVM": Pipeline([
            ("scaler", StandardScaler()),
            (
                "svc",
                CalibratedClassifierCV(
                    SVC(kernel="rbf", C=10, gamma="scale", random_state=RANDOM_SEED), ensemble=False
                ),
            ),
        ]),
    }

    results = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        results[name] = {"model": model, "preds": preds, "accuracy": acc}
        print(f"{name} test accuracy: {acc:.4f}")

    best_name = max(results, key=lambda n: results[n]["accuracy"])
    best = results[best_name]
    print(f"\nBest model: {best_name} (accuracy {best['accuracy']:.4f})\n")

    print(f"=== Classification report ({best_name}) ===")
    print(classification_report(y_test, best["preds"], labels=classes, zero_division=0))

    cm = confusion_matrix(y_test, best["preds"], labels=classes)
    print("=== Confusion matrix (rows = true label, columns = predicted) ===")
    print("           " + " ".join(f"{label:>9}" for label in classes))
    for label, row in zip(classes, cm):
        print(f"{label:>10} " + " ".join(f"{v:>9}" for v in row))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": best["model"],
            "classes": classes,
            "model_name": best_name,
            "fixed_frames": FIXED_FRAMES,
            "vocabulary_source": "kaggle-asl-signs-subset-18-words (proof of concept, not MS-ASL)",
        },
        MODEL_PATH,
    )
    print(f"\nSaved best model ({best_name}) to: {MODEL_PATH}")

    fig, ax = plt.subplots(figsize=(11, 11))
    ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classes).plot(
        ax=ax, xticks_rotation="vertical", colorbar=False
    )
    ax.set_title(f"{best_name} confusion matrix (test accuracy {best['accuracy']:.2%})")
    fig.tight_layout()
    fig.savefig(CONFUSION_MATRIX_PNG, dpi=150)
    print(f"Saved confusion matrix plot to: {CONFUSION_MATRIX_PNG}")


if __name__ == "__main__":
    main()
