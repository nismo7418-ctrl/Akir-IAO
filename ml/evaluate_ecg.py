# ml/evaluate_ecg.py — Évaluation & calibration du modèle ECG — AKIR-IAO v21
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
#
# Étape suivante de la finalisation ECG : produire les chiffres qui font passer
# le module d'« expérimental » à « utilisable ». Sans torch ni modèle ici —
# l'outil prend des SORTIES déjà calculées (logits + vérité terrain), que tu
# génères en passant ton modèle une fois sur le jeu de test.
#
# Produit :
#   - sensibilité / spécificité / support PAR CLASSE (canonique, libellés honnêtes) ;
#   - le RAPPEL STEMI groupé (ST_ELEVATION) — métrique bloquante, cible ≥ 95 % ;
#   - la TEMPÉRATURE de calibration (réduit la sur-confiance du softmax) + ECE.
#
# Tout passe par clinical.ecg_labels.resolve_code — cohérence avec la taxonomie.

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

from clinical.ecg_labels import resolve_code, display_name

STEMI_TARGET = "ST_ELEVATION"   # rappel groupé sur ce code canonique


# ─────────────────────────────────────────────────────────────────────────────
# Outils numériques (pur stdlib — pas de numpy, pas de souci numpy 2.x)
# ─────────────────────────────────────────────────────────────────────────────

def softmax(logits: Sequence[float], temperature: float = 1.0) -> List[float]:
    if temperature <= 0:
        raise ValueError("Température doit être > 0.")
    m = max(logits)
    exps = [math.exp((x - m) / temperature) for x in logits]
    s = sum(exps) or 1.0
    return [e / s for e in exps]


# ─────────────────────────────────────────────────────────────────────────────
# Métriques par classe (un-contre-tous), sur codes canoniques
# ─────────────────────────────────────────────────────────────────────────────

def _canon(labels: Sequence[str]) -> List[str]:
    return [resolve_code(l) for l in labels]


def per_class_metrics(
    y_true: Sequence[str], y_pred: Sequence[str]
) -> Dict[str, Dict[str, float]]:
    """Sensibilité, spécificité et support par classe canonique."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true et y_pred de longueurs différentes.")
    yt, yp = _canon(y_true), _canon(y_pred)
    classes = sorted(set(yt) | set(yp))
    out: Dict[str, Dict[str, float]] = {}
    for c in classes:
        tp = sum(1 for t, p in zip(yt, yp) if t == c and p == c)
        fn = sum(1 for t, p in zip(yt, yp) if t == c and p != c)
        fp = sum(1 for t, p in zip(yt, yp) if t != c and p == c)
        tn = sum(1 for t, p in zip(yt, yp) if t != c and p != c)
        support = tp + fn
        sens = tp / (tp + fn) if (tp + fn) else float("nan")
        spec = tn / (tn + fp) if (tn + fp) else float("nan")
        out[c] = {"sensitivity": sens, "specificity": spec,
                  "support": support, "tp": tp, "fn": fn, "fp": fp, "tn": tn}
    return out


def group_recall(y_true: Sequence[str], y_pred: Sequence[str],
                 target_code: str = STEMI_TARGET) -> float:
    """Rappel pour un code groupé (ex. tous les STEMI — ST_ELEVATION)."""
    yt, yp = _canon(y_true), _canon(y_pred)
    tp = sum(1 for t, p in zip(yt, yp) if t == target_code and p == target_code)
    fn = sum(1 for t, p in zip(yt, yp) if t == target_code and p != target_code)
    return tp / (tp + fn) if (tp + fn) else float("nan")


def confusion_matrix(
    y_true: Sequence[str], y_pred: Sequence[str]
) -> Tuple[List[str], List[List[int]]]:
    yt, yp = _canon(y_true), _canon(y_pred)
    classes = sorted(set(yt) | set(yp))
    idx = {c: i for i, c in enumerate(classes)}
    mat = [[0] * len(classes) for _ in classes]
    for t, p in zip(yt, yp):
        mat[idx[t]][idx[p]] += 1
    return classes, mat


# ─────────────────────────────────────────────────────────────────────────────
# Calibration — temperature scaling (sur jeu de VALIDATION)
# ─────────────────────────────────────────────────────────────────────────────

def _mean_nll(val_logits: Sequence[Sequence[float]],
              true_idx: Sequence[int], temperature: float) -> float:
    tot = 0.0
    for logits, ti in zip(val_logits, true_idx):
        p = softmax(logits, temperature)[ti]
        tot += -math.log(max(p, 1e-12))
    return tot / len(val_logits)


def _ece(val_logits: Sequence[Sequence[float]], true_idx: Sequence[int],
         temperature: float, bins: int = 10) -> float:
    """Expected Calibration Error : écart |confiance - exactitude| par bac."""
    confs, correct = [], []
    for logits, ti in zip(val_logits, true_idx):
        p = softmax(logits, temperature)
        pred = max(range(len(p)), key=p.__getitem__)
        confs.append(p[pred])
        correct.append(1 if pred == ti else 0)
    n = len(confs)
    ece = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        members = [i for i, c in enumerate(confs) if (c > lo and c <= hi) or (b == 0 and c == 0)]
        if not members:
            continue
        acc = sum(correct[i] for i in members) / len(members)
        conf = sum(confs[i] for i in members) / len(members)
        ece += abs(acc - conf) * len(members) / n
    return ece


def calibrate_temperature(
    val_logits: Sequence[Sequence[float]],
    true_idx: Sequence[int],
    t_min: float = 0.5, t_max: float = 5.0, step: float = 0.05,
) -> Dict[str, float]:
    """Cherche la température minimisant la NLL sur le set de validation."""
    if not val_logits:
        raise ValueError("Jeu de validation vide.")
    if len(val_logits) != len(true_idx):
        raise ValueError("logits et labels de longueurs différentes.")

    best_t, best_nll = 1.0, float("inf")
    t = t_min
    while t <= t_max + 1e-9:
        nll = _mean_nll(val_logits, true_idx, t)
        if nll < best_nll:
            best_nll, best_t = nll, round(t, 4)
        t += step
    return {
        "temperature": best_t,
        "nll_before": _mean_nll(val_logits, true_idx, 1.0),
        "nll_after": best_nll,
        "ece_before": _ece(val_logits, true_idx, 1.0),
        "ece_after": _ece(val_logits, true_idx, best_t),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Rapport markdown (à coller dans le model card)
# ─────────────────────────────────────────────────────────────────────────────

def markdown_report(y_true: Sequence[str], y_pred: Sequence[str],
                    calibration: Dict[str, float] | None = None) -> str:
    metrics = per_class_metrics(y_true, y_pred)
    stemi = group_recall(y_true, y_pred)
    lines = ["| Classe | Sensibilité | Spécificité | Support |",
             "|--------|-------------|-------------|---------|"]
    for code, m in sorted(metrics.items()):
        lines.append(
            f"| {display_name(code)[:48]} | {m['sensitivity']:.1%} | "
            f"{m['specificity']:.1%} | {m['support']} |"
        )
    gate = "✅" if (stemi == stemi and stemi >= 0.95) else "❌"
    lines.append("")
    lines.append(f"**Rappel STEMI groupé : {stemi:.1%} {gate}** (cible ≥ 95 %).")
    if calibration:
        lines.append("")
        lines.append(
            f"**Calibration** : T = {calibration['temperature']} — "
            f"ECE {calibration['ece_before']:.3f} — {calibration['ece_after']:.3f}."
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print("Usage : importer per_class_metrics / group_recall / calibrate_temperature")
    print("Entrées attendues : y_true/y_pred (libellés) et, pour la calibration,")
    print("les logits de validation + indices de vérité terrain.")
