"""
ml/train_mortality_model.py — Prédiction de mortalité hospitalière ICU (MIMIC-III)

Données  : data/mimic_mortality_features.csv  (séjours ICU avec vitaux agrégés)
Algo     : GradientBoostingClassifier + Logistic Regression (ensemble)
Features : vitaux agrégés (mean/min/max) + démographiques + contexte admission
Cible    : hospital_expire_flag (0=survie, 1=décès)
Sortie   : ml/mortality_model.joblib

Usage : python ml/train_mortality_model.py
        (lance d'abord : python ml/prepare_mimic_data.py)
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DATA_PATH   = Path("data/mimic_mortality_features.csv")
OUTPUT_PATH = Path("ml/mortality_model.joblib")

# Features sélectionnées — vitaux agrégés + démographie + contexte
FEATURES = [
    # Fréquence cardiaque
    "hr_mean", "hr_min", "hr_max",
    # SpO2
    "spo2_mean", "spo2_min",
    # Fréquence respiratoire
    "rr_mean", "rr_max",
    # Pression artérielle
    "sbp_mean", "sbp_min",
    "dbp_mean",
    "map_mean", "map_min",
    # Température (°C)
    "temp_c_mean", "temp_c_max",
    # Pression veineuse centrale
    "cvp_mean",
    # Features dérivées
    "shock_index",
    "los_hours",
    # Contexte admission
    "admission_type_enc",
    # Démographie
    "gender_enc",
    "age_approx",
    # Volume de monitoring (proxy sévérité)
    "n_vital_measures",
]

TARGET = "hospital_expire_flag"


def load_data(path: Path = DATA_PATH) -> tuple[np.ndarray, np.ndarray, list[str]]:
    df = pd.read_csv(path)
    missing_cols = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing_cols:
        raise KeyError(f"Colonnes manquantes dans {path}: {missing_cols}")

    available = [f for f in FEATURES if f in df.columns]
    X = df[available].to_numpy(dtype=float)
    y = df[TARGET].to_numpy(dtype=int)
    print(f"Dataset: {len(y)} séjours | features={len(available)} | "
          f"décès={y.sum()} ({y.mean()*100:.1f}%)")
    return X, y, available


def build_pipeline() -> Pipeline:
    """
    Pipeline : imputation médiane → StandardScaler → ensemble GBM + LR.
    L'ensemble soft-voting combine GradientBoosting et LogisticRegression
    pour mieux calibrer les probabilités sur un petit dataset.
    """
    gbm = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        min_samples_leaf=3,
        random_state=42,
    )
    lr = LogisticRegression(
        C=0.5,
        class_weight="balanced",
        max_iter=1000,
        random_state=42,
    )
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=5,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    ensemble = VotingClassifier(
        estimators=[("gbm", gbm), ("lr", lr), ("rf", rf)],
        voting="soft",
        weights=[2, 1, 2],
    )
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
        ("clf",     ensemble),
    ])


def train(output_path: Path = OUTPUT_PATH) -> Pipeline:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"{DATA_PATH} introuvable.\n"
            "Lance d'abord : python ml/prepare_mimic_data.py"
        )

    X, y, feature_names = load_data()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"\nEntraînement (train={len(y_train)}, test={len(y_test)})…")
    pipe = build_pipeline()
    pipe.fit(X_train, y_train)

    # ── Évaluation ────────────────────────────────────────────────────────────
    y_pred  = pipe.predict(X_test)
    y_proba = pipe.predict_proba(X_test)[:, 1]

    print("\n=== Rapport de classification ===")
    print(classification_report(y_test, y_pred,
          target_names=["Survie", "Décès"],
          zero_division=0))
    print("=== Matrice de confusion ===")
    print(confusion_matrix(y_test, y_pred))

    if len(np.unique(y_test)) > 1:
        auc = roc_auc_score(y_test, y_proba)
        print(f"\nAUC-ROC (test): {auc:.3f}")

    cv     = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc")
    print(f"AUC CV-5 : {scores.mean():.3f} ± {scores.std():.3f}")

    # ── Feature importance via GBM interne ────────────────────────────────────
    try:
        gbm_clf = pipe.named_steps["clf"].estimators_[0][1]  # GBM dans VotingClassifier
        importances = gbm_clf.feature_importances_
        print("\n=== Top 10 features (GBM) ===")
        for feat, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1])[:10]:
            print(f"  {feat:25s}: {imp:.3f}")
    except Exception:
        pass

    # ── Export ────────────────────────────────────────────────────────────────
    bundle = {"pipeline": pipe, "feature_names": feature_names}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, output_path)
    print(f"\nModèle exporté → {output_path}")
    return pipe


if __name__ == "__main__":
    train()
