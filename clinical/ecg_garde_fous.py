# clinical/ecg_garde_fous.py — Garde-fous cliniques ECG (fonction pure) — AKIR-IAO v21
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
#
# Pourquoi un module séparé : la sûreté ne doit JAMAIS dépendre de torch/du modèle.
# `ml/ecg_predictor.py` produit un dict {label: probabilité} ; ce module applique
# ensuite les règles cliniques absolues. Il est testable sans le moindre poids ML.
#
# Contrat (cf. glossaire ia_ecg) :
#   R1 — Tout signe critique (STEMI, TV, FV, BAV3, HYPERK) avec p ≥ 0.30 force P1,
#        MÊME s'il n'est pas la classe gagnante.
#   R2 — Top non-normal avec confiance < 0.40 — priorité au moins P3 (jamais P4/P5).
#   R0 — Âge < 16 ans — abstention (modèle PTB-XL adulte, non validé en pédiatrie).
#
# Préséance explicite (corrige le risque relevé à l'audit) :
#   R0 (abstention) > R1 (override P1 critique) > R2 (plancher P3) > priorité de base.
#
# ⚠️ Les libellés STEMI/NSTEMI doivent se lire « sus-décalage ST / ischémie » :
#    l'ECG seul ne distingue pas un NSTEMI (diagnostic troponine). Outil d'aide —
#    confirmation cardiologue obligatoire.

from __future__ import annotations

from typing import Dict, Optional, Any

from clinical.ecg_labels import classify as _classify, is_normal, data_support

CRITICAL_THRESHOLD = 0.30   # R1
CONFIDENCE_FLOOR   = 0.40   # R2
PEDIATRIC_AGE      = 16     # R0

# Priorité numérique : 1 = plus urgent … 5 = non urgent.
_P1, _P2, _P3, _P4 = 1, 2, 3, 4


def _norm_label(label: str) -> str:  # conservé pour compat éventuelle externe
    from clinical.ecg_labels import _norm
    return _norm(label)


def apply_ecg_garde_fous(
    probabilities: Dict[str, float],
    *,
    age_years: Optional[float] = None,
    critical_threshold: float = CRITICAL_THRESHOLD,
    confidence_floor: float = CONFIDENCE_FLOOR,
) -> Dict[str, Any]:
    """Applique les garde-fous cliniques à une distribution de probabilités ECG.

    Returns un dict :
        priorite       : int 1..5  | None si abstention/erreur
        priorite_ml    : int       | priorité brute (classe gagnante, sans règle)
        top_label      : str
        top_proba      : float
        override       : str|None  | message si une règle a modifié la priorité
        critical_flags : list[str] | signes critiques ≥ seuil détectés
        abstain        : bool
        erreur         : str|None
    """
    base = {
        "priorite": None, "priorite_ml": None, "top_label": None, "top_proba": None,
        "override": None, "critical_flags": [], "abstain": False, "erreur": None,
    }

    # ── Validation ────────────────────────────────────────────────────────
    if not isinstance(probabilities, dict) or not probabilities:
        return {**base, "erreur": "Distribution de probabilités vide ou invalide."}
    try:
        probs = {str(k): float(v) for k, v in probabilities.items()}
    except (TypeError, ValueError):
        return {**base, "erreur": "Probabilités non numériques."}
    if any(p < 0 for p in probs.values()):
        return {**base, "erreur": "Probabilité négative."}

    top_label = max(probs, key=probs.get)
    top_proba = probs[top_label]
    _, priorite_ml = _classify(top_label)

    # ── R0 — Abstention pédiatrique (prime sur tout) ──────────────────────
    if age_years is not None and age_years < PEDIATRIC_AGE:
        return {
            **base,
            "priorite_ml": priorite_ml,
            "top_label": top_label, "top_proba": top_proba,
            "data_support": data_support(top_label),
            "abstain": True,
            "override": (
                f"ECG pédiatrique (< {PEDIATRIC_AGE} ans) — modèle non validé, "
                "interprétation médicale requise."
            ),
        }

    final = priorite_ml
    override = None

    # ── R1 — Override critique (≥ seuil, même si non gagnant) ──────────────
    critical_flags = []
    for label, p in probs.items():
        is_crit, _ = _classify(label)
        if is_crit and p >= critical_threshold:
            critical_flags.append(f"{label} ({p:.0%})")
    if critical_flags:
        final = _P1
        override = (
            "Signe critique ≥ {:.0%} — priorité forcée P1 : {}".format(
                critical_threshold, ", ".join(critical_flags)
            )
        )

    # ── R2 — Plancher P3 si top non-normal peu confiant (ne réduit pas R1) ─
    elif not is_normal(top_label) and top_proba < confidence_floor:
        if final > _P3:                      # P4/P5 — remonté à P3
            final = _P3
            override = (
                f"Confiance {top_proba:.0%} < {confidence_floor:.0%} sur un tracé "
                "non-normal — priorité plancher P3."
            )

    return {
        "priorite": final,
        "priorite_ml": priorite_ml,
        "top_label": top_label,
        "top_proba": top_proba,
        "override": override,
        "critical_flags": critical_flags,
        "data_support": data_support(top_label),
        "abstain": False,
        "erreur": None,
    }
