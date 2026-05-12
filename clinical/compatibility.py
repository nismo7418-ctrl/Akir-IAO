"""Compatibilité IV en Y — matrice HUG.

La source opérationnelle est la matrice HUG déjà intégrée dans
``data/pharmacie_rea.json`` via ``clinical.pharmaco_rea``. Ce module fournit une
API stable pour les autres onglets, avec normalisation des noms usuels de PSE.
"""
from __future__ import annotations

import unicodedata
from typing import Any

from clinical.pharmaco_rea import check_compatibility as _lookup_hug_pair


_PERFUSION_ALIASES = {
    "morphine pse": "morphine",
    "morphine": "morphine",
    "dipidolor": "piritramide",
    "piritramide": "piritramide",
    "ketamine": "kétamine",
    "kétamine": "kétamine",
    "midazolam": "midazolam",
    "hypnovel": "midazolam",
    "adrenaline": "épinéphrine",
    "adrénaline": "épinéphrine",
    "epinephrine": "épinéphrine",
    "épinéphrine": "épinéphrine",
    "noradrenaline": "noradrénaline",
    "noradrénaline": "noradrénaline",
    "dobutamine": "dobutamine",
    "amiodarone": "amiodarone",
    "labetalol": "labétalol",
    "labétalol": "labétalol",
    "nicardipine": "nicardipine",
    "magnesium": "magnésium",
    "magnésium": "magnésium",
    "insuline": "insuline rapide",
    "insuline rapide": "insuline rapide",
    "furosémide": "furosémide",
    "furosemide": "furosémide",
    "heparine": "héparine sodique",
    "héparine": "héparine sodique",
}


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.replace("®", "").replace("—", " ").replace("/", " ").split())


def normalize_med_name(name: str) -> str:
    """Retourne un nom compatible avec les libellés HUG lorsque possible."""
    n = _norm(name)
    if not n:
        return ""
    for alias, canonical in _PERFUSION_ALIASES.items():
        if _norm(alias) in n:
            return canonical
    return str(name or "").strip().casefold()


def med_from_perfusion_choice(choice: str) -> str:
    """Extrait le médicament canonique depuis le libellé du calculateur PSE."""
    if not choice or "sélectionner" in _norm(choice):
        return ""
    return normalize_med_name(choice.split("—", 1)[0])


def check_iv_compatibility(med_a: str, med_b: str) -> dict[str, Any]:
    """Retourne Compatible / Incompatible / Prudence pour une paire IV en Y."""
    a = normalize_med_name(med_a)
    b = normalize_med_name(med_b)
    result = {
        "med_a": a or med_a,
        "med_b": b or med_b,
        "statut": "Prudence",
        "code": "?",
        "message": "Donnée HUG absente: vérifier avec la pharmacie avant administration en Y.",
        "precision": "",
        "reference": "HUG CompatAdm DCI",
        "raw": None,
    }
    if not a or not b:
        result["message"] = "Sélectionner deux médicaments IV pour contrôler la compatibilité en Y."
        return result
    if a == b:
        result.update({
            "statut": "Compatible",
            "code": "C",
            "message": "Même substance sélectionnée.",
        })
        return result

    raw = _lookup_hug_pair(a, b)
    if not raw:
        return result

    code = raw.get("statut", "?")
    if code == "C":
        status = "Compatible"
        message = f"{a} + {b}: compatible selon la matrice HUG."
    elif code == "I":
        status = "Incompatible"
        message = f"{a} + {b}: risque de précipitation/incompatibilité en Y."
    else:
        status = "Prudence"
        message = f"{a} + {b}: compatible seulement sous conditions HUG."

    result.update({
        "med_a": raw.get("substance_A") or a,
        "med_b": raw.get("substance_B") or b,
        "statut": status,
        "code": code,
        "message": message,
        "precision": raw.get("precision") or "",
        "reference": raw.get("reference") or "HUG CompatAdm DCI",
        "raw": raw,
    })
    return result


__all__ = [
    "check_iv_compatibility",
    "med_from_perfusion_choice",
    "normalize_med_name",
]
