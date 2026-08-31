"""
Trains a gesture classifier on the normalized hand-landmark features in
data/processed/gesture_landmarks.csv, compares RandomForest vs SVM on a
held-out test split, and saves the better-performing model to
data/models/gesture_classifier.pkl. Run from backend/:

    venv/bin/python scripts/train_gesture_classifier.py
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
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

BACKEND_ROOT = Path(__file__).resolve().parent.parent
FEATURES_CSV = BACKEND_ROOT / "data" / "processed" / "gesture_landmarks.csv"
MODEL_PATH = BACKEND_ROOT / "data" / "models" / "gesture_classifier.pkl"
CONFUSION_MATRIX_PNG = BACKEND_ROOT / "data" / "processed" / "confusion_matrix.png"

# "nothing" means no hand was detected — that's an upstream presence check,
# not a gesture the classifier should predict.
EXCLUDED_CLASSES = {"nothing"}
TEST_SIZE = 0.2
RANDOM_SEED = 42


def load_dataset() -> tuple[np.ndarray, np.ndarray]:
    with open(FEATURES_CSV, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # header
        rows = [row for row in reader if row[0] not in EXCLUDED_CLASSES]

    labels = np.array([row[0] for row in rows])
    features = np.array([[float(v) for v in row[1:]] for row in rows])
    return features, labels


def main():
    if not FEATURES_CSV.exists():
        raise FileNotFoundError(
            f"Feature CSV not found: {FEATURES_CSV}. Run prepare_gesture_dataset.py first."
        )

    X, y = load_dataset()
    classes = sorted(set(y))
    print(f"Loaded {len(y)} samples across {len(classes)} classes (excluded: {sorted(EXCLUDED_CLASSES)})")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )
    print(f"Train: {len(y_train)} samples, Test: {len(y_test)} samples\n")

    candidates = {
        "RandomForest": RandomForestClassifier(n_estimators=200, random_state=RANDOM_SEED, n_jobs=-1),
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

    print("=== Classification report ({}) ===".format(best_name))
    print(classification_report(y_test, best["preds"], labels=classes, zero_division=0))

    cm = confusion_matrix(y_test, best["preds"], labels=classes)
    print("=== Confusion matrix (rows = true label, columns = predicted) ===")
    print("      " + " ".join(f"{label:>5}" for label in classes))
    for label, row in zip(classes, cm):
        print(f"{label:>5} " + " ".join(f"{v:>5}" for v in row))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": best["model"], "classes": classes, "model_name": best_name}, MODEL_PATH)
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
