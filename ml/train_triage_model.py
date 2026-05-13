"""
ml/train_triage_model.py — Classifieur de triage AKIR-IAO v2
Données  : data/triage_enriched.csv  (KTAS réel, 1267 patients)
           + augmentation synthétique P1/P5 pour rééquilibrage
Algo     : Random Forest (class_weight='balanced')
Features : 13 — vitales brutes + contexte + features dérivées
Sortie   : ml/triage_rf_model.joblib

Usage : python ml/train_triage_model.py
"""

from __future__ import annotations

import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

DATA_PATH          = Path("data/triage_enriched.csv")
MIMIC_ENRICH_PATH  = Path("data/mimic_triage_enrichment.csv")
OUTPUT_PATH        = Path("ml/triage_rf_model.joblib")

FEATURES = [
    "fc", "fr", "pas", "pad", "spo2", "temp",
    "avpu_enc", "nrs_pain", "arrival_ambulance", "injury",
    "shock_index", "map_val", "pp",
]
TARGET = "priorite"

RNG = np.random.default_rng(42)

# ── Augmentation synthétique ──────────────────────────────────────────────────

_SYNTH_SPECS = {
    1: {  # Déchocage — P1 sévèrement sous-représenté (26 cas réels)
        "fc_mu": 125, "fc_sd": 40,
        "fr_mu": 28,  "fr_sd": 8,
        "pas_mu": 75, "pas_sd": 20,
        "spo2_mu": 82, "spo2_sd": 8,
        "temp_mu": 38.8, "temp_sd": 1.5,
        "avpu_probs": [0.10, 0.20, 0.35, 0.35],
        "nrs_mu": 6.0, "nrs_sd": 3.0,
        "p_ambulance": 0.80,
        "p_injury": 0.40,
        "pad_ratio": 0.55,
    },
    5: {  # Non-urgent — P5 aussi limité (75 cas réels)
        "fc_mu": 72,  "fc_sd": 10,
        "fr_mu": 14,  "fr_sd": 2,
        "pas_mu": 125, "pas_sd": 15,
        "spo2_mu": 98, "spo2_sd": 1,
        "temp_mu": 36.8, "temp_sd": 0.4,
        "avpu_probs": [1.00, 0.00, 0.00, 0.00],
        "nrs_mu": 1.5, "nrs_sd": 1.5,
        "p_ambulance": 0.05,
        "p_injury": 0.05,
        "pad_ratio": 0.68,
    },
}


def _synth_cohort(prio: int, n: int) -> pd.DataFrame:
    s = _SYNTH_SPECS[prio]
    fc  = np.clip(RNG.normal(s["fc_mu"],  s["fc_sd"],  n), 20, 250)
    fr  = np.clip(RNG.normal(s["fr_mu"],  s["fr_sd"],  n), 4,  60)
    pas = np.clip(RNG.normal(s["pas_mu"], s["pas_sd"], n), 40, 260)
    pad = np.clip(pas * RNG.normal(s["pad_ratio"], 0.04, n), 20, 160)
    spo2 = np.clip(RNG.normal(s["spo2_mu"], s["spo2_sd"], n), 50, 100)
    temp = np.clip(RNG.normal(s["temp_mu"], s["temp_sd"], n), 33.0, 42.5)
    avpu = RNG.choice([0, 1, 2, 3], n, p=s["avpu_probs"])
    nrs  = np.clip(RNG.normal(s["nrs_mu"], s["nrs_sd"], n), 0, 10)
    amb  = RNG.binomial(1, s["p_ambulance"], n)
    inj  = RNG.binomial(1, s["p_injury"], n)

    si = fc / np.where(pas > 0, pas, 1)
    mv = (pas + 2 * pad) / 3
    pp = pas - pad

    return pd.DataFrame({
        "fc": fc, "fr": fr, "pas": pas, "pad": pad,
        "spo2": spo2, "temp": temp,
        "avpu_enc": avpu, "nrs_pain": nrs,
        "arrival_ambulance": amb, "injury": inj,
        "shock_index": si, "map_val": mv, "pp": pp,
        TARGET: prio,
    })


# ── Chargement données réelles ────────────────────────────────────────────────

def load_real_data(path: Path = DATA_PATH) -> pd.DataFrame | None:
    if not path.exists():
        return None
    df = pd.read_csv(path)
    missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing:
        print(f"⚠️  Colonnes manquantes dans {path}: {missing}")
        return None
    return df[FEATURES + [TARGET]].dropna()


def load_mimic_enrichment(path: Path = MIMIC_ENRICH_PATH) -> pd.DataFrame | None:
    """
    Charge les vitaux ICU MIMIC-III comme exemples P1/P2 réels.
    Filtre les colonnes disponibles pour correspondre à FEATURES.
    """
    if not path.exists():
        return None
    df = pd.read_csv(path)
    available = [c for c in FEATURES + [TARGET] if c in df.columns]
    missing   = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing:
        print(f"  MIMIC enrichment — colonnes absentes (imputées): {missing}")
    df_sub = df[available].copy()
    # Imputer les colonnes manquantes par des valeurs neutres
    for col in FEATURES:
        if col not in df_sub.columns:
            df_sub[col] = 0.0
    df_sub = df_sub[FEATURES + [TARGET]].dropna(subset=["fc", "fr", "pas", "spo2", TARGET])
    print(f"  MIMIC enrichment : {len(df_sub)} séjours ICU réels "
          f"(P1={( df_sub[TARGET]==1).sum()}, P2={(df_sub[TARGET]==2).sum()})")
    return df_sub


# ── Pipeline d'entraînement ───────────────────────────────────────────────────

def train(output_path: Path = OUTPUT_PATH) -> RandomForestClassifier:
    real_df = load_real_data()

    if real_df is not None:
        print(f"Données KTAS réelles chargées : {len(real_df)} patients")
        dist = real_df[TARGET].value_counts().sort_index().to_dict()
        print(f"  Distribution KTAS : {dist}")

        # Enrichissement MIMIC-III (vitaux ICU réels → P1/P2)
        mimic_df = load_mimic_enrichment()

        # Augmentation synthétique P1/P5 pour rééquilibrer les extrêmes
        synth_p1 = _synth_cohort(1, 200)
        synth_p5 = _synth_cohort(5, 200)

        parts = [real_df, synth_p1, synth_p5]
        if mimic_df is not None:
            parts.append(mimic_df)

        df = pd.concat(parts, ignore_index=True)
        n_mimic = len(mimic_df) if mimic_df is not None else 0
        print(f"  Après augmentation (synth P1/P5 + {n_mimic} MIMIC) : {len(df)} patients")
        source = f"KTAS réel + MIMIC-III + augmentation synthétique"
    else:
        print("⚠️  triage_enriched.csv introuvable — génération 100 % synthétique")
        print("   Lance d'abord : python nettoyage_IA.py")
        # Fallback : jeu entièrement synthétique (comportement v1)
        from ml._synth_fallback import generate_training_data_v2
        df = generate_training_data_v2()
        source = "synthétique (fallback)"

    X = df[FEATURES].to_numpy(dtype=float)
    y = df[TARGET].to_numpy(dtype=int)

    dist_final = {k: int(v) for k, v in zip(*np.unique(y, return_counts=True))}
    print(f"\nDistribution finale {dist_final}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"\nEntraînement Random Forest ({source})…")
    clf = RandomForestClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # ── Évaluation ────────────────────────────────────────────────────────────
    y_pred = clf.predict(X_test)
    print("\n=== Rapport de classification ===")
    print(classification_report(y_test, y_pred,
          target_names=[f"P{i}" for i in range(1, 6)],
          zero_division=0))

    print("=== Matrice de confusion ===")
    print(confusion_matrix(y_test, y_pred))

    cv     = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(clf, X, y, cv=cv, scoring="f1_weighted")
    print(f"\nF1 CV-5 : {scores.mean():.3f} ± {scores.std():.3f}")

    print("\n=== Importance des features ===")
    for feat, imp in sorted(zip(FEATURES, clf.feature_importances_), key=lambda x: -x[1]):
        print(f"  {feat:20s}: {imp:.3f}")

    # ── Export ────────────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, output_path)
    print(f"\nModèle exporté → {output_path}")
    return clf


if __name__ == "__main__":
    train()
