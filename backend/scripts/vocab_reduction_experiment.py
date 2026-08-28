"""
Quick experiment: does restricting the Intermediate Conversational
Fluency vocabulary to only the classes with enough real MS-ASL samples
get us to a materially better, more honestly deployable accuracy than
trying to keep all 30 words?

Reuses the exact same load/augment/feature/model code as
improve_msasl_classifier.py so results are apples-to-apples; just
filters the label set by a minimum total-sample-count threshold before
running the same val-selected, test-reported evaluation.

Run from backend/:
    python3 scripts/vocab_reduction_experiment.py
"""
import time

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from improve_msasl_classifier import (
    RANDOM_SEED,
    augment_dataset,
    flatten_features,
    load_dataset,
    pooled_features,
)

seqs, labels, splits = load_dataset()

from collections import Counter
total_counts = Counter(labels)

for MIN_COUNT in (10, 15, 20, 25):
    keep_classes = {c for c, n in total_counts.items() if n >= MIN_COUNT}
    mask = np.isin(labels, list(keep_classes))
    seqs_f, labels_f, splits_f = seqs[mask], labels[mask], splits[mask]
    classes = sorted(keep_classes)

    train_mask, val_mask, test_mask = splits_f == "train", splits_f == "val", splits_f == "test"
    seq_train, y_train_real = seqs_f[train_mask], labels_f[train_mask]
    seq_val, y_val = seqs_f[val_mask], labels_f[val_mask]
    seq_test, y_test = seqs_f[test_mask], labels_f[test_mask]

    if len(seq_val) == 0 or len(seq_test) == 0 or len(seq_train) == 0:
        print(f"MIN_COUNT={MIN_COUNT}: {len(classes)} classes -- skipping, empty split")
        continue

    aug_seq, aug_labels = augment_dataset(seq_train, y_train_real, per_sample=4)
    seq_train_aug = np.concatenate([seq_train, aug_seq], axis=0)
    y_train_aug = np.concatenate([y_train_real, aug_labels], axis=0)

    classifiers = {
        "RandomForest": lambda: RandomForestClassifier(
            n_estimators=400, max_depth=18, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1
        ),
        "HistGradBoosting": lambda: HistGradientBoostingClassifier(
            max_iter=150, max_depth=4, learning_rate=0.1, random_state=RANDOM_SEED
        ),
        "SVM_rbf": lambda: Pipeline([
            ("scaler", StandardScaler()),
            ("svc", SVC(kernel="rbf", C=8, gamma="scale", random_state=RANDOM_SEED)),
        ]),
        "LogReg": lambda: Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=3000, C=1.0, random_state=RANDOM_SEED)),
        ]),
    }
    feature_builders = {"raw_flatten": flatten_features, "pooled_stats": pooled_features}
    train_variants = {"no_aug": (seq_train, y_train_real), "with_aug": (seq_train_aug, y_train_aug)}

    best = None
    for fname, fbuild in feature_builders.items():
        Xval = fbuild(seq_val)
        for tname, (seq_t, y_t) in train_variants.items():
            Xtrain = fbuild(seq_t)
            for cname, cbuild in classifiers.items():
                t0 = time.time()
                model = cbuild()
                model.fit(Xtrain, y_t)
                val_acc = accuracy_score(y_val, model.predict(Xval))
                if best is None or val_acc > best[0]:
                    best = (val_acc, fname, tname, cname)

    val_acc, fname, tname, cname = best
    fbuild = feature_builders[fname]
    seq_t, y_t = train_variants[tname]
    seq_trainval = np.concatenate([seq_t, seq_val], axis=0)
    y_trainval = np.concatenate([y_t, y_val], axis=0)
    final_model = classifiers[cname]()
    final_model.fit(fbuild(seq_trainval), y_trainval)
    test_acc = accuracy_score(y_test, final_model.predict(fbuild(seq_test)))

    print(
        f"MIN_COUNT={MIN_COUNT:2d} | {len(classes):2d} classes | train={len(y_train_real):3d} "
        f"val={len(y_val):3d} test={len(y_test):3d} | best-on-val={fname}/{tname}/{cname} "
        f"(val {val_acc:.3f}) | TEST ACC = {test_acc:.4f}",
        flush=True,
    )
