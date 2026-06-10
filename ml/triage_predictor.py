"""
ml/triage_predictor.py — Inférence du classifieur de triage AKIR-IAO v2
Fonction publique : get_ml_priority(data) → dict

Features du modèle (13) :
    fc, fr, pas, pad, spo2, temp        — vitales brutes
    avpu_enc                             — encodage AVPU 0-3
    nrs_pain                             — douleur 0-10 (0 si non évaluable)
    arrival_ambulance                    — 0/1
    injury                               — 0/1
    shock_index, map_val, pp             — features dérivées (calculées ici)

Encodage AVPU :
    "A" (Alert)        → 0
    "V" (Voice)        → 1
    "P" (Pain)         → 2
    "U" (Unresponsive) → 3
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

_LOG = logging.getLogger(__name__)

_MODEL_PATH = Path(__file__).parent / "triage_rf_model.joblib"

_AVPU_MAP: dict[str, int] = {"A": 0, "V": 1, "P": 2, "U": 3}

FEATURES = [
    "fc", "fr", "pas", "pad", "spo2", "temp",
    "avpu_enc", "nrs_pain", "arrival_ambulance", "injury",
    "shock_index", "map_val", "pp",
]

_PRIORITY_LABELS: dict[int, tuple[str, str]] = {
    1: ("P1 — Déchocage immédiat",   "#EF4444"),
    2: ("P2 — Très urgent",          "#F97316"),
    3: ("P3 — Urgent",               "#EAB308"),
    4: ("P4 — Peu urgent",           "#22C55E"),
    5: ("P5 — Non urgent",           "#64748B"),
}

_clf = None


def _load_model():
    global _clf
    if _clf is not None:
        return _clf
    if not _MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modèle introuvable : {_MODEL_PATH}\n"
            "Lance d'abord : python ml/train_triage_model.py"
        )
    import joblib
    _clf = joblib.load(_MODEL_PATH)
    _LOG.info("Modèle triage v2 chargé depuis %s", _MODEL_PATH)
    return _clf


def _encode_avpu(avpu: Any) -> int:
    if isinstance(avpu, (int, float)):
        return int(np.clip(avpu, 0, 3))
    return _AVPU_MAP.get(str(avpu).strip().upper(), 0)


def get_ml_priority(data: dict) -> dict:
    """
    Prédit la priorité de triage.

    Args (dict) — obligatoires :
        fc, fr, pas, spo2, temp   – vitales numériques
        avpu                       – "A"/"V"/"P"/"U" ou 0-3
        news2                      – score NEWS2 (accepté pour compat., non utilisé par le modèle v2)

    Args optionnels (nouvelles features v2) :
        pad                        – pression diastolique (défaut : pas × 0.65)
        nrs_pain                   – douleur 0-10 (défaut : 0)
        arrival_ambulance          – 0/1 (défaut : 0)
        injury                     – 0/1 (défaut : 0)

    Returns dict :
        priorite, label, couleur, probabilites, confiance, alerte_p1,
        features_input, erreur
    """
    try:
        clf = _load_model()
    except FileNotFoundError as exc:
        return _error_result(str(exc))

    try:
        fc    = float(data.get("fc",   80))
        fr    = float(data.get("fr",   16))
        pas   = float(data.get("pas",  120))
        spo2  = float(data.get("spo2", 98))
        temp  = float(data.get("temp", 37.0))
        avpu  = _encode_avpu(data.get("avpu", "A"))

        # Nouvelles features optionnelles
        pad  = float(data.get("pad", pas * 0.65))   # DBP estimé si absent
        nrs  = float(data.get("nrs_pain", 0))
        amb  = int(bool(data.get("arrival_ambulance", 0)))
        inj  = int(bool(data.get("injury", 0)))

        # Features dérivées
        si = fc / pas if pas > 0 else 1.0
        mv = (pas + 2 * pad) / 3
        pp = pas - pad

    except (TypeError, ValueError) as exc:
        return _error_result(f"Valeur invalide : {exc}")

    row = np.array([[fc, fr, pas, pad, spo2, temp,
                     avpu, nrs, amb, inj,
                     si, mv, pp]])

    # Vérification compatibilité feature count
    expected = len(FEATURES)
    if hasattr(clf, "n_features_in_") and clf.n_features_in_ != expected:
        return _error_result(
            f"Modèle entraîné sur {clf.n_features_in_} features, "
            f"prédicteur en envoie {expected}. "
            "Ré-entraîne le modèle : python ml/train_triage_model.py"
        )

    prio_ml = int(clf.predict(row)[0])
    proba   = clf.predict_proba(row)[0]

    classes  = list(clf.classes_)
    prob_map = {int(c): float(p) for c, p in zip(classes, proba)}

    # ── Garde-fous cliniques (overrides absolus KTAS) ─────────────────────────
    prio_pred, override_rule = _apply_clinical_overrides(
        prio_ml, fc=fc, pas=pas, spo2=spo2, avpu=avpu,
    )

    confiance = prob_map.get(prio_pred, 0.0)
    alerte_p1 = prio_pred == 1 or prob_map.get(1, 0.0) >= 0.25

    label, couleur = _PRIORITY_LABELS.get(prio_pred, ("Inconnu", "#64748B"))

    return {
        "priorite":      prio_pred,
        "priorite_ml":   prio_ml,
        "label":         label,
        "couleur":       couleur,
        "probabilites":  prob_map,
        "confiance":     confiance,
        "alerte_p1":     alerte_p1,
        "override":      override_rule,
        "features_input": {
            "fc": fc, "fr": fr, "pas": pas, "pad": pad,
            "spo2": spo2, "temp": temp, "avpu": avpu,
            "nrs_pain": nrs, "arrival_ambulance": amb, "injury": inj,
            "shock_index": round(si, 3), "map_val": round(mv, 1), "pp": round(pp, 1),
        },
        "erreur": None,
    }


# ── Garde-fous cliniques absolus ─────────────────────────────────────────────

def _apply_clinical_overrides(
    prio_ml: int, *, fc: float, pas: float, spo2: float, avpu: int,
) -> tuple[int, str | None]:
    """
    Surcharge la prédiction ML par des règles cliniques absolues KTAS.
    Retourne (priorité_finale, libellé_règle | None si aucune règle déclenchée).
    L'ordre est important : on évalue de la règle la plus critique à la moins.
    """
    # Règle 1 — Arrêt cardio-respiratoire : FC et PAS à 0 → P1 immédiat
    if fc == 0 and pas == 0:
        return 1, "ACR — FC et PAS nuls"

    # Règle 2 — Altération majeure de conscience (AVPU = U) → P1 immédiat
    if avpu >= 3:
        return 1, "AVPU = U (inconscient)"

    # Règle 3 — Hypoxie critique SpO2 < 75 % → P1 (au-delà de la simple sévérité)
    if spo2 < 75:
        return 1, "Hypoxie critique (SpO₂ < 75 %)"

    # Règle 4 — Hypoxie sévère SpO2 < 85 % → minimum P2
    if spo2 < 85 and prio_ml >= 3:
        return 2, "Hypoxie sévère (SpO₂ < 85 %)"

    return prio_ml, None


def _error_result(msg: str) -> dict:
    return {
        "priorite": None, "label": "—", "couleur": "#64748B",
        "probabilites": {}, "confiance": 0.0,
        "alerte_p1": False, "features_input": {}, "erreur": msg,
    }


if __name__ == "__main__":
    import json

    cas_tests = [
        # Choc compensé — P1 attendu malgré FC normale
        {"fc": 82, "fr": 22, "pas": 72, "pad": 40, "spo2": 94, "temp": 37.2,
         "nrs_pain": 8, "arrival_ambulance": 1, "injury": 0, "avpu": "A"},
        # AVPU=U — P1 attendu
        {"fc": 90, "fr": 16, "pas": 120, "pad": 75, "spo2": 97, "temp": 36.9,
         "nrs_pain": 0, "arrival_ambulance": 1, "injury": 0, "avpu": "U"},
        # Patient stable — P5 attendu
        {"fc": 72, "fr": 14, "pas": 125, "pad": 80, "spo2": 99, "temp": 36.7,
         "nrs_pain": 2, "arrival_ambulance": 0, "injury": 0, "avpu": "A"},
        # Détresse respiratoire — P2
        {"fc": 110, "fr": 28, "pas": 95, "pad": 60, "spo2": 88, "temp": 38.5,
         "nrs_pain": 7, "arrival_ambulance": 1, "injury": 0, "avpu": "V"},
        # Compatibilité API v1 (sans pad/nrs_pain/injury) — doit fonctionner
        {"fc": 88, "fr": 18, "pas": 110, "spo2": 95, "temp": 37.5,
         "news2": 4, "avpu": "A"},
    ]

    for i, cas in enumerate(cas_tests, 1):
        res = get_ml_priority(cas)
        if res["erreur"]:
            print(f"Test {i}: ERREUR — {res['erreur']}")
        else:
            si = res["features_input"].get("shock_index", "?")
            print(f"Test {i}: {res['label']}  (confiance {res['confiance']:.0%})"
                  f"  alerte_P1={res['alerte_p1']}"
                  f"  SI={si:.2f}"
                  f"  probas={json.dumps({k: f'{v:.2f}' for k, v in res['probabilites'].items()})}")
