"""
ml/readmission_predictor.py — Inférence du risque de réadmission J30

Fonction publique : predict_readmission(data) → dict

Features attendues (dict) :
    age                   – int  (années)
    gender                – int  (0=M, 1=F, 2=Autre)
    cholesterol           – int  (mg/dL)
    bmi                   – float
    diabetes              – int  (0/1)
    hypertension          – int  (0/1)
    medication_count      – int
    length_of_stay        – int  (jours)
    systolic              – int  (mmHg)
    diastolic             – int  (mmHg)
    discharge_destination – str  ("Home" | "Rehab" | "Nursing_Facility")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

_LOG = logging.getLogger(__name__)

_MODEL_PATH = Path(__file__).parent / "readmission_rf_model.joblib"

# Seuils de risque (probabilité de réadmission J30)
_RISK_LEVELS = [
    (0.40, "Élevé",   "#EF4444", "⚠️"),
    (0.20, "Modéré",  "#F97316", "🔶"),
    (0.00, "Faible",  "#22C55E", "✅"),
]

FEATURES_NUM = [
    "age", "gender", "cholesterol", "bmi",
    "diabetes", "hypertension", "medication_count",
    "length_of_stay", "systolic", "diastolic",
]
FEATURE_CAT  = ["discharge_destination"]

_bundle = None  # {"clf": ..., "enc": ...}


def _load():
    global _bundle
    if _bundle is not None:
        return _bundle
    if not _MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modèle introuvable : {_MODEL_PATH}\n"
            "Lance d'abord : python ml/train_readmission_model.py"
        )
    import joblib
    _bundle = joblib.load(_MODEL_PATH)
    _LOG.info("Modèle réadmission chargé depuis %s", _MODEL_PATH)
    return _bundle


def _risk_level(proba: float) -> tuple[str, str, str]:
    for threshold, label, color, icon in _RISK_LEVELS:
        if proba >= threshold:
            return label, color, icon
    return "Faible", "#22C55E", "✅"


def predict_readmission(data: dict[str, Any]) -> dict:
    """
    Prédit le risque de réadmission à 30 jours.

    Returns dict :
        probabilite          – float 0-1
        risque               – str "Faible" | "Modéré" | "Élevé"
        couleur              – hex CSS
        icone                – emoji
        facteurs_principaux  – list[dict] top-3 features les plus influentes
        features_input       – dict des valeurs utilisées
        erreur               – str | None
    """
    try:
        bundle = _load()
    except FileNotFoundError as exc:
        return _error_result(str(exc))

    clf = bundle["clf"]
    enc = bundle["enc"]

    try:
        dest = str(data.get("discharge_destination", "Home"))
        dest_enc = enc.transform([[dest]])[0][0]

        row = np.array([[
            float(data.get("age",              50)),
            float(data.get("gender",            0)),
            float(data.get("cholesterol",      200)),
            float(data.get("bmi",             25.0)),
            float(data.get("diabetes",          0)),
            float(data.get("hypertension",      0)),
            float(data.get("medication_count",  0)),
            float(data.get("length_of_stay",    1)),
            float(data.get("systolic",        120)),
            float(data.get("diastolic",        80)),
            float(dest_enc),
        ]])
    except (TypeError, ValueError) as exc:
        return _error_result(f"Valeur invalide : {exc}")

    proba = float(clf.predict_proba(row)[0][1])
    risque, couleur, icone = _risk_level(proba)

    # Top-3 features par importance × valeur normalisée
    all_features = FEATURES_NUM + FEATURE_CAT
    importances  = clf.feature_importances_
    top_idx      = np.argsort(importances)[::-1][:3]
    facteurs = [
        {"feature": all_features[i], "importance": float(importances[i])}
        for i in top_idx
    ]

    return {
        "probabilite":         proba,
        "risque":              risque,
        "couleur":             couleur,
        "icone":               icone,
        "facteurs_principaux": facteurs,
        "features_input":      {k: data.get(k) for k in FEATURES_NUM + FEATURE_CAT},
        "erreur":              None,
    }


def _error_result(msg: str) -> dict:
    return {
        "probabilite": None, "risque": "—", "couleur": "#64748B",
        "icone": "❓", "facteurs_principaux": [], "features_input": {}, "erreur": msg,
    }


if __name__ == "__main__":
    cas = [
        {"age": 74, "gender": 1, "cholesterol": 240, "bmi": 31.5, "diabetes": 1,
         "hypertension": 0, "medication_count": 5, "length_of_stay": 1,
         "systolic": 130, "diastolic": 72, "discharge_destination": "Nursing_Facility"},
        {"age": 35, "gender": 0, "cholesterol": 180, "bmi": 23.0, "diabetes": 0,
         "hypertension": 0, "medication_count": 1, "length_of_stay": 2,
         "systolic": 118, "diastolic": 76, "discharge_destination": "Home"},
    ]
    for i, c in enumerate(cas, 1):
        r = predict_readmission(c)
        print(f"Patient {i}: {r['icone']} {r['risque']} — {r['probabilite']:.1%}")
