"""
ml/mortality_predictor.py — Prédiction de mortalité hospitalière ICU

Fonction publique : predict_mortality(data) → dict

Features attendues (dict, toutes optionnelles avec défauts cliniques) :
    hr_mean, hr_min, hr_max          — fréquence cardiaque (bpm)
    spo2_mean, spo2_min              — saturation O2 (%)
    rr_mean, rr_max                  — fréquence respiratoire (/min)
    sbp_mean, sbp_min                — pression systolique (mmHg)
    dbp_mean                         — pression diastolique (mmHg)
    map_mean, map_min                — pression artérielle moyenne (mmHg)
    temp_c_mean, temp_c_max          — température (°C)
    cvp_mean                         — pression veineuse centrale (mmHg)
    shock_index                      — FC/PAS (calculé si absent)
    los_hours                        — durée de séjour (heures)
    admission_type_enc               — 0=électif, 1=urgent, 2=urgence
    gender_enc                       — 0=H, 1=F
    age_approx                       — âge (années)
    n_vital_measures                 — nombre de mesures vitaux (proxy monitoring)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

_LOG = logging.getLogger(__name__)
_MODEL_PATH = Path(__file__).parent / "mortality_model.joblib"

# Valeurs par défaut (patient ICU typique)
_DEFAULTS: dict[str, float] = {
    "hr_mean": 88.0,   "hr_min": 60.0,   "hr_max": 120.0,
    "spo2_mean": 96.0, "spo2_min": 92.0,
    "rr_mean": 18.0,   "rr_max": 22.0,
    "sbp_mean": 115.0, "sbp_min": 90.0,
    "dbp_mean": 65.0,
    "map_mean": 82.0,  "map_min": 65.0,
    "temp_c_mean": 37.0, "temp_c_max": 37.8,
    "cvp_mean": 8.0,
    "shock_index": 0.77,
    "los_hours": 48.0,
    "admission_type_enc": 2.0,
    "gender_enc": 0.0,
    "age_approx": 65.0,
    "n_vital_measures": 200.0,
}

# Seuils de risque
_RISK_LEVELS = [
    (0.60, "Très élevé", "#DC2626", "🔴"),
    (0.35, "Élevé",      "#EF4444", "⚠️"),
    (0.15, "Modéré",     "#F97316", "🔶"),
    (0.00, "Faible",     "#22C55E", "✅"),
]

_bundle = None


def _load():
    global _bundle
    if _bundle is not None:
        return _bundle
    if not _MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modèle introuvable : {_MODEL_PATH}\n"
            "Lance d'abord : python ml/train_mortality_model.py"
        )
    import joblib
    _bundle = joblib.load(_MODEL_PATH)
    _LOG.info("Modèle mortalité ICU chargé depuis %s", _MODEL_PATH)
    return _bundle


def _risk_level(proba: float) -> tuple[str, str, str]:
    for threshold, label, color, icon in _RISK_LEVELS:
        if proba >= threshold:
            return label, color, icon
    return "Faible", "#22C55E", "✅"


def predict_mortality(data: dict[str, Any]) -> dict:
    """
    Prédit le risque de mortalité hospitalière.

    Returns dict :
        probabilite         — float 0-1
        risque              — str
        couleur             — hex CSS
        icone               — str
        score_sofa_proxy    — float (approximation SOFA depuis vitaux)
        facteurs_alarme     — list[str] signes de gravité détectés
        features_input      — dict des valeurs utilisées
        erreur              — str | None
    """
    try:
        bundle = _load()
    except FileNotFoundError as exc:
        return _error_result(str(exc))

    pipe         = bundle["pipeline"]
    feature_names = bundle["feature_names"]

    try:
        # Calculer shock_index si non fourni
        if "shock_index" not in data or data["shock_index"] is None:
            hr  = float(data.get("hr_mean", _DEFAULTS["hr_mean"]))
            sbp = float(data.get("sbp_mean", _DEFAULTS["sbp_mean"]))
            data["shock_index"] = hr / sbp if sbp > 0 else _DEFAULTS["shock_index"]

        row_vals = []
        features_used = {}
        for feat in feature_names:
            val = data.get(feat)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                val = _DEFAULTS.get(feat, np.nan)
            val = float(val)
            row_vals.append(val)
            features_used[feat] = val

        row = np.array([row_vals])

    except (TypeError, ValueError) as exc:
        return _error_result(f"Valeur invalide : {exc}")

    proba  = float(pipe.predict_proba(row)[0][1])
    risque, couleur, icone = _risk_level(proba)

    # ── Signes d'alarme cliniques ─────────────────────────────────────────────
    alarmes = []
    if features_used.get("shock_index", 0) > 1.0:
        alarmes.append("Index de choc > 1 (choc compensé probable)")
    if features_used.get("spo2_min", 100) < 90:
        alarmes.append(f"SpO2 min {features_used['spo2_min']:.0f}% — hypoxémie sévère")
    if features_used.get("sbp_min", 120) < 80:
        alarmes.append(f"PAS min {features_used['sbp_min']:.0f} mmHg — hypotension franche")
    if features_used.get("map_min", 80) < 65:
        alarmes.append(f"PAM min {features_used['map_min']:.0f} mmHg — seuil sepsis")
    if features_used.get("rr_max", 16) > 28:
        alarmes.append(f"FR max {features_used['rr_max']:.0f}/min — détresse respiratoire")
    if features_used.get("hr_max", 80) > 130:
        alarmes.append(f"FC max {features_used['hr_max']:.0f} bpm — tachycardie sévère")
    temp_max = features_used.get("temp_c_max", 37.0)
    if temp_max > 39.5:
        alarmes.append(f"Température max {temp_max:.1f}°C — hyperthermie")
    elif features_used.get("temp_c_mean", 37.0) < 36.0:
        alarmes.append(f"Température moy {features_used['temp_c_mean']:.1f}°C — hypothermie")

    # ── Score SOFA proxy (approximation à partir des vitaux disponibles) ───────
    sofa_proxy = _compute_sofa_proxy(features_used)

    return {
        "probabilite":      proba,
        "risque":           risque,
        "couleur":          couleur,
        "icone":            icone,
        "score_sofa_proxy": sofa_proxy,
        "facteurs_alarme":  alarmes,
        "features_input":   features_used,
        "erreur":           None,
    }


def _compute_sofa_proxy(f: dict) -> float:
    """Approximation SOFA (0-24) à partir des vitaux agrégés."""
    score = 0.0

    # Cardiovasculaire (MAP)
    map_m = f.get("map_mean", 80)
    if map_m < 65:
        score += 4
    elif map_m < 70:
        score += 2

    # Respiratoire (SpO2 comme proxy PaO2/FiO2)
    spo2 = f.get("spo2_mean", 97)
    if spo2 < 88:
        score += 4
    elif spo2 < 92:
        score += 3
    elif spo2 < 95:
        score += 1

    # Neurologique (shock_index comme proxy état de conscience)
    si = f.get("shock_index", 0.7)
    if si > 1.5:
        score += 4
    elif si > 1.0:
        score += 2

    return round(score, 1)


def _error_result(msg: str) -> dict:
    return {
        "probabilite": None, "risque": "—", "couleur": "#64748B",
        "icone": "❓", "score_sofa_proxy": None,
        "facteurs_alarme": [], "features_input": {}, "erreur": msg,
    }


if __name__ == "__main__":
    cas = [
        {   # Patient critique — choc septique
            "hr_mean": 118, "hr_min": 95, "hr_max": 145,
            "spo2_mean": 89, "spo2_min": 82,
            "rr_mean": 28, "rr_max": 35,
            "sbp_mean": 78, "sbp_min": 58,
            "dbp_mean": 42, "map_mean": 54, "map_min": 44,
            "temp_c_mean": 38.9, "temp_c_max": 40.2,
            "los_hours": 24, "admission_type_enc": 2,
            "age_approx": 72, "gender_enc": 1, "n_vital_measures": 800,
        },
        {   # Patient stable post-opératoire
            "hr_mean": 72, "hr_min": 58, "hr_max": 88,
            "spo2_mean": 98, "spo2_min": 96,
            "rr_mean": 14, "rr_max": 18,
            "sbp_mean": 128, "sbp_min": 108,
            "dbp_mean": 74, "map_mean": 92, "map_min": 78,
            "temp_c_mean": 36.9, "temp_c_max": 37.4,
            "los_hours": 12, "admission_type_enc": 0,
            "age_approx": 52, "gender_enc": 0, "n_vital_measures": 150,
        },
    ]
    for i, c in enumerate(cas, 1):
        r = predict_mortality(c)
        if r["erreur"]:
            print(f"Patient {i}: ERREUR — {r['erreur']}")
        else:
            print(f"Patient {i}: {r['icone']} {r['risque']} — {r['probabilite']:.1%} "
                  f"| SOFA proxy={r['score_sofa_proxy']}"
                  f"{'  | ' + ' / '.join(r['facteurs_alarme'][:2]) if r['facteurs_alarme'] else ''}")
