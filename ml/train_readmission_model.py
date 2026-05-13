"""
ml/train_readmission_model.py — Classifieur de risque de réadmission J30
Données  : data/readmissions_clean.csv  (30 000 patients, 12.2 % réadmis)
Algo     : Random Forest avec class_weight='balanced'
Sortie   : ml/readmission_rf_model.joblib

Usage : python ml/train_readmission_model.py
"""

from __future__ import annotations

import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import OrdinalEncoder

DATA_PATH   = Path("data/readmissions_clean.csv")
OUTPUT_PATH = Path("ml/readmission_rf_model.joblib")

FEATURES_NUM = [
    "age", "gender", "cholesterol", "bmi",
    "diabetes", "hypertension", "medication_count",
    "length_of_stay", "systolic", "diastolic",
]
FEATURE_CAT  = ["discharge_destination"]
TARGET       = "readmitted_30_days"

# Encodage ordinal fixe pour discharge_destination
DEST_CATEGORIES = [["Home", "Rehab", "Nursing_Facility"]]


def load_and_prepare(path: Path) -> tuple[np.ndarray, np.ndarray, OrdinalEncoder]:
    df = pd.read_csv(path)

    enc = OrdinalEncoder(categories=DEST_CATEGORIES, handle_unknown="use_encoded_value", unknown_value=-1)
    df["discharge_destination"] = enc.fit_transform(df[["discharge_destination"]])

    X = df[FEATURES_NUM + FEATURE_CAT].to_numpy(dtype=float)
    y = df[TARGET].to_numpy(dtype=int)
    return X, y, enc


def train(output_path: Path = OUTPUT_PATH) -> RandomForestClassifier:
    print("Chargement des données…")
    X, y, enc = load_and_prepare(DATA_PATH)
    print(f"  {len(y)} patients | réadmis: {y.sum()} ({y.mean()*100:.1f} %)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print("Entraînement Random Forest…")
    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # ── Évaluation ────────────────────────────────────────────────────────────
    y_pred  = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    print("\n=== Rapport de classification ===")
    print(classification_report(y_test, y_pred, target_names=["Non réadmis", "Réadmis J30"]))
    print("=== Matrice de confusion ===")
    print(confusion_matrix(y_test, y_pred))
    print(f"\nAUC-ROC : {roc_auc_score(y_test, y_proba):.3f}")

    cv    = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(clf, X, y, cv=cv, scoring="roc_auc")
    print(f"AUC CV-5 : {scores.mean():.3f} ± {scores.std():.3f}")

    print("\n=== Importance des features ===")
    all_features = FEATURES_NUM + FEATURE_CAT
    for feat, imp in sorted(zip(all_features, clf.feature_importances_), key=lambda x: -x[1]):
        print(f"  {feat:25s}: {imp:.3f}")

    # ── Export — on sérialise aussi l'encodeur pour l'inférence ───────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"clf": clf, "enc": enc}, output_path)
    print(f"\nModèle exporté → {output_path}")
    return clf


if __name__ == "__main__":
    train()
