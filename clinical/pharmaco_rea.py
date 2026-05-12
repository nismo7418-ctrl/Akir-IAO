# clinical/pharmaco_rea.py — Base de données REA : dilutions & compatibilités en Y
# Source 1 : Protocole dilutions standardisées intraveineuses continues (Hainaut)
# Source 2 : HUG_CompatAdm_DCI — Pharmacie HUG, révision 10.08.2018
from __future__ import annotations

import json
import logging
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)
_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "pharmacie_rea.json"


def _empty_db() -> dict[str, Any]:
    return {"metadata": {}, "dilutions": [], "compatibilites_y": []}


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    """Charge la base REA sans faire planter l'onglet Pharmacie."""
    try:
        with _JSON_PATH.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        _LOG.warning("Base pharmacie REA introuvable: %s", _JSON_PATH)
        return _empty_db()
    except json.JSONDecodeError as exc:
        _LOG.error("JSON pharmacie REA invalide (%s): %s", _JSON_PATH, exc)
        return _empty_db()
    except OSError as exc:
        _LOG.error("Lecture impossible de la base pharmacie REA (%s): %s", _JSON_PATH, exc)
        return _empty_db()

    if not isinstance(raw, dict):
        _LOG.error("Structure pharmacie REA invalide: racine JSON non objet")
        return _empty_db()

    data = _empty_db()
    data["metadata"] = raw.get("metadata", {})

    dilutions = raw.get("dilutions", [])
    if isinstance(dilutions, list):
        data["dilutions"] = [d for d in dilutions if isinstance(d, dict)]
    else:
        _LOG.error("Structure pharmacie REA invalide: 'dilutions' non liste")

    compatibilites = raw.get("compatibilites_y", [])
    if isinstance(compatibilites, list):
        data["compatibilites_y"] = [
            e for e in compatibilites if isinstance(e, dict)
        ]
    else:
        _LOG.error("Structure pharmacie REA invalide: 'compatibilites_y' non liste")

    return data


def _norm(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", str(text or "").casefold())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _dilution_search_values(entry: dict[str, Any]) -> list[str]:
    adaptation = entry.get("adaptation_belge", {})
    if not isinstance(adaptation, dict):
        adaptation = {}
    noms_be = adaptation.get("noms_commerciaux_be", [])
    if not isinstance(noms_be, list):
        noms_be = []

    values = [
        entry.get("id", ""),
        entry.get("nom_source", ""),
        entry.get("DCI", ""),
        entry.get("classe_therapeutique", ""),
        adaptation.get("DCI", ""),
    ]
    values.extend(str(nom) for nom in noms_be)
    return [str(v) for v in values if v]


# ── Dilutions ─────────────────────────────────────────────────────────────────

def get_dilutions() -> list[dict]:
    return _load().get("dilutions", [])


def search_dilutions(query: str) -> list[dict]:
    if not query or not query.strip():
        return get_dilutions()
    q = _norm(query)
    return [
        d for d in get_dilutions()
        if any(q in _norm(value) for value in _dilution_search_values(d))
    ]


def get_dilution(query: str) -> dict | None:
    """Retourne la meilleure dilution pour un nom, DCI, ID ou nom belge."""
    if not query or not str(query).strip():
        return None

    q = _norm(query)
    for entry in get_dilutions():
        if any(q == _norm(value) for value in _dilution_search_values(entry)):
            return entry

    matches = search_dilutions(query)
    return matches[0] if matches else None


# ── Compatibilités en Y ───────────────────────────────────────────────────────

def get_compatibilites() -> list[dict]:
    return [
        e for e in _load().get("compatibilites_y", [])
        if e.get("substance_A") and e.get("substance_B") and e.get("statut")
    ]


def _compat_names(entry: dict[str, Any], side: str) -> set[str]:
    return {
        _norm(entry.get(f"substance_{side}", "")),
        _norm(entry.get(f"DCI_{side}", "")),
    } - {""}


def get_substances_list() -> list[str]:
    """Retourne toutes les substances uniques (noms) du tableau de compatibilité."""
    subs: set[str] = set()
    for e in get_compatibilites():
        if e.get("substance_A"):
            subs.add(e["substance_A"])
        if e.get("substance_B"):
            subs.add(e["substance_B"])
    return sorted(subs)


def lookup_compat(sub_a: str, sub_b: str) -> dict | None:
    """Cherche la compatibilité pour une paire, dans les deux sens."""
    a, b = _norm(sub_a), _norm(sub_b)
    if not a or not b:
        return None

    for e in get_compatibilites():
        names_a = _compat_names(e, "A")
        names_b = _compat_names(e, "B")
        if (a in names_a and b in names_b) or (a in names_b and b in names_a):
            return e
    return None


def check_compatibility(sub_a: str, sub_b: str) -> dict | None:
    """Alias métier explicite pour l'interface et les futurs appels externes."""
    return lookup_compat(sub_a, sub_b)


def get_all_compat_for(substance: str) -> list[dict]:
    """Retourne toutes les paires connues impliquant une substance donnée."""
    s = _norm(substance)
    if not s:
        return []

    return [
        e for e in get_compatibilites()
        if s in _compat_names(e, "A") or s in _compat_names(e, "B")
    ]


def get_partner(entry: dict, substance: str) -> tuple[str, str]:
    """
    Pour une entrée de compatibilité, retourne (substance_partenaire, DCI_partenaire).
    Permet de savoir quelle est l'autre molécule de la paire.
    """
    s = _norm(substance)
    if s in _compat_names(entry, "A"):
        return entry.get("substance_B", ""), entry.get("DCI_B", "")
    return entry.get("substance_A", ""), entry.get("DCI_A", "")


__all__ = [
    "get_dilutions",
    "get_dilution",
    "search_dilutions",
    "get_compatibilites",
    "get_substances_list",
    "lookup_compat",
    "check_compatibility",
    "get_all_compat_for",
    "get_partner",
]
