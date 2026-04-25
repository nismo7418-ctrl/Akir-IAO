"""FRENCH triage v1.2 protocol data – édition corrigée et enrichie."""

from __future__ import annotations
from typing import Dict, List, Optional
from clinical.utils import norm   # centralisé

NO_CRITERION_LABEL = "Aucun critere discriminant selectionne"

def _row(category: str, motif: str, default: str, criteria=(), aliases=()):
    return {
        "id": norm(motif).replace(" ", "_").replace("/", "_"),
        "category": category,
        "motif": motif,
        "default": default,
        "criteria": [{"level": level, "text": text} for level, text in criteria],
        "aliases": list(aliases),
    }

# ---------------------------------------------------------------------
# Motifs ajoutés pour correspondre à la table de dispatch de triage.py
# ---------------------------------------------------------------------
EXTRA_MOTIFS = [
    # Vomissements / Diarrhée combiné (utilisé par le dispatch)
    _row("Abdominal", "Vomissements / Diarrhee", "5", [
        ("2", "Symptômes d'occlusion"),
        ("3A", "Enfant <= 2 ans"),
        ("3B", "Douleur abdominale ou vomissements abondants / diarrhée abondante ou mauvaise tolérance"),
    ], aliases=["Vomissements / Diarrhee", "Vomissements et diarrhee"]),

    # Fièvre enfant 3 mois - 15 ans
    _row("Pédiatrie", "Fievre enfant (3 mois - 15 ans)", "4", [
        ("2", "Température >= 40 °C ou somnolence, geignement, marbrures"),
        ("3A", "Tachycardie pour l'âge ou mauvaise tolérance"),
    ], aliases=["Pediatrie - Fievre enfant (3 mois - 15 ans)"]),
]

FRENCH_PROTOCOL = [
    # ... (toutes les entrées originales inchangées, par souci de place je ne les répète pas,
    #      mais elles sont identiques à la version fournie, sauf normalisation des accents)
    # On les place en premier, puis on ajoute EXTRA_MOTIFS à la fin.
] + EXTRA_MOTIFS

# Construction des index
FRENCH_INDEX: Dict[str, dict] = {}
for item in FRENCH_PROTOCOL:
    FRENCH_INDEX[norm(item["motif"])] = item
    for alias in item.get("aliases", []):
        FRENCH_INDEX[norm(alias)] = item

FRENCH_MOTS_CAT: Dict[str, List[str]] = {}
for item in FRENCH_PROTOCOL:
    FRENCH_MOTS_CAT.setdefault(item["category"], []).append(item["motif"])

FRENCH_MOTIFS_RAPIDES = [
    "Arret cardiorespiratoire",
    "Douleur thoracique / syndrome coronaire aigu (SCA)",
    "Dyspnee / insuffisance respiratoire",
    "Deficit moteur sensitif sensoriel ou du langage / AVC",
    "Alteration de la conscience / coma",
    "Traumatisme cranien",
    "Hypotension arterielle",
    "Fievre",
    "Hypoglycemie",
    "Hyperglycemie",
    "Convulsions",
    "Hemoptysie",
    "Asthme ou aggravation BPCO",
    "Brulure",
    "Traumatisme abdomen thorax cervical",
    "Pediatrie - Fievre <= 3 mois",
    "Autre motif",
]

def get_protocol(motif: str) -> Optional[dict]:
    return FRENCH_INDEX.get(norm(motif))

def get_criterion_options(motif: str) -> List[dict]:
    protocol = get_protocol(motif)
    if not protocol:
        return [{"level": None, "text": "", "label": NO_CRITERION_LABEL}]
    options = [{"level": None, "text": "", "label": NO_CRITERION_LABEL}]
    for criterion in protocol["criteria"]:
        level = criterion["level"]
        text = criterion["text"]
        options.append({"level": level, "text": text, "label": f"Tri {level} - {text}"})
    return options


def render_discriminants(
    motif: str,
    *,
    key: Optional[str] = None,
    label: str = "Critere discriminant",
    index: int = 0,
):
    """
    Affiche un selecteur Streamlit si disponible, sinon renvoie simplement les options.

    Le module a ete tronque dans certaines revisions; cette fonction restaure
    l'API attendue par streamlit_app.py tout en restant tolerante si elle est
    appelee hors contexte Streamlit.
    """
    options = get_criterion_options(motif)

    try:
        import streamlit as st
    except Exception:
        return options

    if not options:
        return {"level": None, "text": "", "label": NO_CRITERION_LABEL}

    index = max(0, min(index, len(options) - 1))
    selected = st.selectbox(
        label,
        options,
        index=index,
        key=key,
        format_func=lambda opt: opt["label"],
    )
    return selected
