"""
Trains the Intermediate Conversational Fluency temporal sign classifier
on data/processed/msasl_intermediate_landmarks.csv (produced by
prepare_msasl_dataset.py), using MS-ASL's own train/val/test split
(assigned by the dataset's creators, not re-split here) — a more
rigorous held-out evaluation than a self-constructed split. Compares
RandomForest vs SVM on the val split for model selection, reports final
numbers on the untouched test split, and saves the better model to
data/models/msasl_intermediate_classifier.pkl.

Run from backend/:
    venv/bin/python scripts/train_msasl_classifier.py
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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from app.services.word_landmark_features import FIXED_FRAMES

BACKEND_ROOT = Path(__file__).resolve().parent.parent
COURSE = "intermediate"
FEATURES_CSV = BACKEND_ROOT / "data" / "processed" / f"msasl_{COURSE}_landmarks.csv"
MODEL_PATH = BACKEND_ROOT / "data" / "models" / f"msasl_{COURSE}_classifier.pkl"
CONFUSION_MATRIX_PNG = BACKEND_ROOT / "data" / "processed" / f"msasl_{COURSE}_confusion_matrix.png"

RANDOM_SEED = 42


def load_dataset():
    with open(FEATURES_CSV, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # header
        rows = list(reader)

    labels = np.array([row[0] for row in rows])
    splits = np.array([row[1] for row in rows])
    features = np.array([[float(v) for v in row[4:]] for row in rows])
    return features, labels, splits


def main():
    if not FEATURES_CSV.exists():
        raise FileNotFoundError(f"Feature CSV not found: {FEATURES_CSV}. Run prepare_msasl_dataset.py first.")

    X, y, splits = load_dataset()
    classes = sorted(set(y))
    print(f"Loaded {len(y)} samples across {len(classes)} classes")
    for s in ("train", "val", "test"):
        print(f"  {s}: {(splits == s).sum()} samples")

    X_train, y_train = X[splits == "train"], y[splits == "train"]
    X_val, y_val = X[splits == "val"], y[splits == "val"]
    X_test, y_test = X[splits == "test"], y[splits == "test"]

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

    val_results = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        val_preds = model.predict(X_val)
        val_acc = accuracy_score(y_val, val_preds)
        val_results[name] = {"model": model, "val_accuracy": val_acc}
        print(f"{name} validation accuracy: {val_acc:.4f}")

    best_name = max(val_results, key=lambda n: val_results[n]["val_accuracy"])
    best_model = val_results[best_name]["model"]
    print(f"\nBest model on validation: {best_name} (val accuracy {val_results[best_name]['val_accuracy']:.4f})\n")

    test_preds = best_model.predict(X_test)
    test_acc = accuracy_score(y_test, test_preds)
    print(f"=== Final test accuracy ({best_name}): {test_acc:.4f} (n={len(y_test)}) ===\n")

    print(f"=== Classification report on TEST split ({best_name}) ===")
    print(classification_report(y_test, test_preds, labels=classes, zero_division=0))

    cm = confusion_matrix(y_test, test_preds, labels=classes)
    print("=== Confusion matrix on TEST split (rows = true label, columns = predicted) ===")
    print("           " + " ".join(f"{label[:9]:>9}" for label in classes))
    for label, row in zip(classes, cm):
        print(f"{label[:10]:>10} " + " ".join(f"{v:>9}" for v in row))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": best_model,
            "classes": classes,
            "model_name": best_name,
            "fixed_frames": FIXED_FRAMES,
            "vocabulary_source": f"MS-ASL {COURSE} curriculum (C-UDA 0.1 licensed, research/computational use only)",
            "test_accuracy": test_acc,
        },
        MODEL_PATH,
    )
    print(f"\nSaved best model ({best_name}) to: {MODEL_PATH}")

    fig, ax = plt.subplots(figsize=(13, 13))
    ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classes).plot(
        ax=ax, xticks_rotation="vertical", colorbar=False
    )
    ax.set_title(f"{best_name} test-split confusion matrix (accuracy {test_acc:.2%})")
    fig.tight_layout()
    fig.savefig(CONFUSION_MATRIX_PNG, dpi=150)
    print(f"Saved confusion matrix plot to: {CONFUSION_MATRIX_PNG}")


if __name__ == "__main__":
    main()
