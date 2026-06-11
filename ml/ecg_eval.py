# ml/ecg_eval.py — Évaluation & calibration du modèle ECG — AKIR-IAO v21
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
#
# Répond au point bloquant de l'audit : « l'accuracy ne suffit pas — c'est la
# SENSIBILITÉ PAR CLASSE, surtout le rappel STEMI, qui décide si le modèle est
# déployable ». Plus la calibration de température, sans laquelle les seuils
# 30 %/40 % des garde-fous ne valent rien.
#
# Pur Python (pas de torch, pas de numpy) — testable et léger. Tu fournis :
#   - y_true   : liste des libellés vrais
#   - y_pred   : liste des libellés prédits (argmax)
#   - logits   : (optionnel) liste de vecteurs de logits, pour la calibration
# et tu obtiens des chiffres à coller dans le model card.

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple, Any

# Seuil de sûreté : un infarctus raté est catastrophique.
MIN_STEMI_SENSITIVITY = 0.95

# Familles de libellés (compatibles libellés hérités ET canoniques).
STEMI_GROUP = {"STEMI_ANT", "STEMI_INF", "STEMI_LAT", "ST_ELEVATION", "STEMI"}


# ─────────────────────────────────────────────────────────────────────────────
# Matrice de confusion & métriques par classe
# ─────────────────────────────────────────────────────────────────────────────

def confusion_matrix(
    y_true: Sequence[str], y_pred: Sequence[str], labels: List[str]
) -> List[List[int]]:
    """Matrice [vrai][prédit] indexée selon l'ordre de `labels`."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true et y_pred doivent avoir la même longueur.")
    idx = {l: i for i, l in enumerate(labels)}
    m = [[0] * len(labels) for _ in labels]
    for t, p in zip(y_true, y_pred):
        if t in idx and p in idx:
            m[idx[t]][idx[p]] += 1
    return m


def per_class_metrics(
    y_true: Sequence[str], y_pred: Sequence[str], labels: List[str]
) -> Dict[str, Dict[str, Optional[float]]]:
    """Sensibilité (rappel), spécificité et support par classe."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true et y_pred doivent avoir la même longueur.")
    out: Dict[str, Dict[str, Optional[float]]] = {}
    for c in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == c and p == c)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == c and p != c)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != c and p == c)
        tn = sum(1 for t, p in zip(y_true, y_pred) if t != c and p != c)
        out[c] = {
            "sensitivity": tp / (tp + fn) if (tp + fn) else None,
            "specificity": tn / (tn + fp) if (tn + fp) else None,
            "support": tp + fn,
        }
    return out


def grouped_sensitivity(
    y_true: Sequence[str], y_pred: Sequence[str], group: set
) -> Optional[float]:
    """Parmi les vrais de la famille, fraction prédite dans la famille.

    Pour le STEMI : on se moque du territoire exact, on veut « détecté ou pas ».
    """
    pos = [(t, p) for t, p in zip(y_true, y_pred) if t in group]
    if not pos:
        return None
    hits = sum(1 for _, p in pos if p in group)
    return hits / len(pos)


# ─────────────────────────────────────────────────────────────────────────────
# Calibration (temperature scaling)
# ─────────────────────────────────────────────────────────────────────────────

def _softmax(logits: Sequence[float], temperature: float = 1.0) -> List[float]:
    if temperature <= 0:
        raise ValueError("La température doit être > 0.")
    m = max(logits)
    exps = [math.exp((x - m) / temperature) for x in logits]
    s = sum(exps) or 1.0
    return [e / s for e in exps]


def negative_log_likelihood(
    logits: Sequence[Sequence[float]], y_idx: Sequence[int], temperature: float = 1.0
) -> float:
    """NLL moyen sous température T (plus bas = mieux calibré)."""
    if not logits:
        raise ValueError("Aucun logit fourni.")
    total = 0.0
    for vec, true_i in zip(logits, y_idx):
        p = _softmax(vec, temperature)[true_i]
        total += -math.log(max(p, 1e-12))
    return total / len(logits)


def fit_temperature(
    logits: Sequence[Sequence[float]],
    y_idx: Sequence[int],
    grid: Optional[Sequence[float]] = None,
) -> Tuple[float, float]:
    """Cherche la température minimisant le NLL. Retourne (T*, NLL*).

    T* > 1 — le modèle était sur-confiant (cas typique des CNN). Les seuils des
    garde-fous doivent être (re)fixés APRÈS application de T*.
    """
    if grid is None:
        grid = [round(0.5 + 0.05 * k, 2) for k in range(0, 91)]  # 0.5 — 5.0
    best_t, best_nll = 1.0, float("inf")
    for t in grid:
        nll = negative_log_likelihood(logits, y_idx, t)
        if nll < best_nll:
            best_t, best_nll = t, nll
    return best_t, best_nll


def expected_calibration_error(
    confidences: Sequence[float], correct: Sequence[bool], n_bins: int = 10
) -> float:
    """ECE : écart moyen |précision − confiance| par bin de confiance."""
    if len(confidences) != len(correct):
        raise ValueError("confidences et correct doivent avoir la même longueur.")
    n = len(confidences)
    if n == 0:
        return 0.0
    ece = 0.0
    for b in range(n_bins):
        lo, hi = b / n_bins, (b + 1) / n_bins
        in_bin = [
            (c, ok) for c, ok in zip(confidences, correct)
            if (c > lo or (b == 0 and c >= lo)) and c <= hi
        ]
        if not in_bin:
            continue
        avg_conf = sum(c for c, _ in in_bin) / len(in_bin)
        acc = sum(1 for _, ok in in_bin if ok) / len(in_bin)
        ece += (len(in_bin) / n) * abs(acc - avg_conf)
    return ece


# ─────────────────────────────────────────────────────────────────────────────
# Gate de déployabilité
# ─────────────────────────────────────────────────────────────────────────────

def safety_gate(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    labels: List[str],
    *,
    min_stemi_sensitivity: float = MIN_STEMI_SENSITIVITY,
) -> Dict[str, Any]:
    """Verdict de déployabilité. Le rappel STEMI est la métrique bloquante."""
    reasons: List[str] = []
    stemi_sens = grouped_sensitivity(y_true, y_pred, STEMI_GROUP)

    if stemi_sens is None:
        reasons.append("Aucun STEMI dans le set de test — sensibilité STEMI non mesurable.")
    elif stemi_sens < min_stemi_sensitivity:
        reasons.append(
            f"Rappel STEMI {stemi_sens:.1%} < cible {min_stemi_sensitivity:.0%} "
            "— risque d'infarctus sous-triés. NON déployable."
        )
    return {
        "deployable": not reasons,
        "stemi_sensitivity": stemi_sens,
        "reasons": reasons or ["Critères de sûreté minimaux atteints (à compléter par revue clinique)."],
    }
