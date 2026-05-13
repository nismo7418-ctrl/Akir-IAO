# clinical/semantic_engine.py — Clinical Semantic Engine v2.0 — AKIR-IAO
# Auteur : Ismail Ibn-Daifa — Hainaut, Belgique
# RGPD : aucune donnée nominative transmise à l'API

from __future__ import annotations

import os
import re
from typing import List, Optional

import anthropic
from pydantic import BaseModel, Field


def _get_api_key() -> str | None:
    """Lit la clé API depuis st.secrets (local / Streamlit Cloud) ou l'env."""
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    except Exception:
        return os.environ.get("ANTHROPIC_API_KEY")

# ══════════════════════════════════════════════════════════════════════════════
# Schéma de sortie Pydantic
# ══════════════════════════════════════════════════════════════════════════════

class Anamnese(BaseModel):
    pqrst_t: Optional[str] = Field(None, description="Temporalité standardisée (ex. 'Début hier (>24h)')")
    pqrst_r: Optional[str] = Field(None, description="Localisation anatomique standardisée")
    pqrst_q: Optional[str] = Field(None, description="Qualité / caractère de la douleur")
    pqrst_s: Optional[str] = Field(None, description="Sévérité estimée (EVA estimée ou qualitative)")
    motif_reformule: Optional[str] = Field(None, description="Motif de consultation réécrit proprement")


class FlagsSysteme(BaseModel):
    news2_target_o2: Optional[str] = Field(None, description="Cible SpO2 selon pathologie (ex. '88-92%' si BPCO)")
    alerte_hemorragique: Optional[bool] = Field(None, description="Risque hémorragique détecté (anticoagulants/AOD)")
    alerte_sepsis: Optional[bool] = Field(None, description="Critères SIRS / sepsis détectés")
    alerte_grossesse: Optional[bool] = Field(None, description="Grossesse connue ou possible mentionnée")
    alerte_allergie: Optional[bool] = Field(None, description="Allergie médicamenteuse mentionnée")
    score_urgence_estime: Optional[str] = Field(None, description="Niveau P1/P2/P3/P4/P5 estimé")


class AnalyseClinique(BaseModel):
    anamnese: Anamnese
    atcd_matching: List[str] = Field(default_factory=list, description="Antécédents identifiés depuis la liste standard")
    traitements_detectes: List[str] = Field(default_factory=list, description="Médicaments / classes thérapeutiques détectés")
    flags_systeme: FlagsSysteme
    confiance: float = Field(0.0, ge=0.0, le=1.0, description="Score de confiance global [0-1]")
    termes_ambigus: List[str] = Field(default_factory=list, description="Termes non résolus ou à clarifier")


# ══════════════════════════════════════════════════════════════════════════════
# System prompt médical — stable → eligible au prompt caching
# ══════════════════════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """Tu es un moteur d'analyse sémantique clinique spécialisé urgences / SMUR. \
Tu reçois une dictée médicale libre, souvent abrégée ou avec des fautes de frappe. \
Ta mission : extraire les entités cliniques avec tolérance aux fautes et expansion sémantique.

## Mappings temporels
- "hier" / "la nuit" / "nuit dernière" → "Début hier (>24h)"
- "ce matin" / "aujourd'hui" / "quelques heures" → "Début récent (<24h)"
- "depuis X jours" → préciser en jours
- "brutal" / "soudain" → "Début brutal"

## Mappings anatomiques
- "hypogastre" / "bas ventre" → "Hypogastre (fosse iliaque médiale)"
- "épigastre" / "estomac" → "Épigastre"
- "FID" / "FIG" → "Fosse iliaque droite / gauche"
- "poitrine" / "thorax" / "sternum" → "Thorax antérieur"
- "dos" / "rachis" → "Rachis / région dorsale"
- "tête" / "céphalée" → "Céphalée (localisation à préciser)"

## Antécédents standard (atcd_matching)
Utilise exclusivement ces étiquettes si elles correspondent :
BPCO, Asthme, Insuffisance cardiaque, Coronaropathie, Fibrillation auriculaire,
Diabète type 1, Diabète type 2, Hypertension, AVC/AIT, Insuffisance rénale chronique,
Néoplasie active, Immunodépression, Grossesse, Anticoagulants / AOD, Antiagrégeants,
Corticothérapie au long cours, Hépatopathie, MICI, Épilepsie, Troubles psychiatriques

## Flags système — règles strictes
- BPCO ou toute bronchopathie obstructive → news2_target_o2 = "88-92%"
- Anticoagulants / AOD / antiagrégants → alerte_hemorragique = true
- Température, frissons, infection → évaluer alerte_sepsis
- Mention grossesse / "enceinte" / "GEU" → alerte_grossesse = true
- Mention allergie → alerte_allergie = true

## Contrainte RGPD impérative
Si des termes identifiants apparaissent (nom, prénom, date de naissance, numéro de registre national, \
adresse), remplace-les par [REDACTED] dans TOUS les champs de sortie. Ne les transmets jamais en clair.

## Format de sortie
Réponds UNIQUEMENT avec le JSON valide correspondant au schéma fourni, sans commentaire ni texte autour.
"""

# ══════════════════════════════════════════════════════════════════════════════
# Pré-traitement RGPD — couche défensive avant envoi à l'API
# ══════════════════════════════════════════════════════════════════════════════

_RGPD_PATTERNS = [
    # Numéro de registre national belge : XX.XX.XX-XXX.XX
    re.compile(r"\b\d{2}[.\-]\d{2}[.\-]\d{2}[.\-]\d{3}[.\-]\d{2}\b"),
    # Date de naissance explicite
    re.compile(r"\b(né|née|ddn|dob)[^\d]*\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b", re.IGNORECASE),
    # Adresse (rue / avenue / boulevard)
    re.compile(r"\b(rue|avenue|av\.|boulevard|bd\.|chaussée|allée)\s+[A-ZÀ-Ü][a-zA-ZÀ-ü\s\-']+\d*\b", re.IGNORECASE),
    # Nom propre heuristique : Prénom NOM consécutifs
    re.compile(r"\b[A-ZÀÈÉÊËÎÏÔÙÛÜ][a-zàèéêëîïôùûü]+\s+[A-ZÀÈÉÊËÎÏÔÙÛÜ]{2,}[a-zàèéêëîïôùûü]*\b"),
]


def _anonymise(texte: str) -> str:
    """Remplace les entités identifiantes par [REDACTED]."""
    for pattern in _RGPD_PATTERNS:
        texte = pattern.sub("[REDACTED]", texte)
    return texte


# ══════════════════════════════════════════════════════════════════════════════
# Moteur principal
# ══════════════════════════════════════════════════════════════════════════════

_TOOL_NAME = "extract_clinical_analysis"

# Schéma JSON dérivé de Pydantic — calculé 1 seule fois au chargement du module
_TOOL_SCHEMA = AnalyseClinique.model_json_schema()


def analyser_dictee(
    dictee: str,
    *,
    api_key: str | None = None,
) -> AnalyseClinique:
    """Parse une dictée médicale libre et retourne un objet AnalyseClinique structuré.

    Args:
        dictee: Texte brut (ex. "hier hypogastre contraction bpco anticoag").
        api_key: Clé API Anthropic. Si None, utilise ANTHROPIC_API_KEY.

    Returns:
        AnalyseClinique validé par Pydantic.

    Raises:
        ValueError: dictée vide ou réponse Claude non parsable.
        anthropic.APIError: erreur de l'API Anthropic (auth, quota, etc.).
    """
    if not dictee or not dictee.strip():
        raise ValueError("La dictée ne peut pas être vide.")

    texte_anonymise = _anonymise(dictee.strip())
    client = anthropic.Anthropic(api_key=api_key or _get_api_key())

    # Tool use → sortie JSON garantie conforme au schéma Pydantic
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[
            {
                "name": _TOOL_NAME,
                "description": "Extrait l'analyse clinique structurée de la dictée IAO.",
                "input_schema": _TOOL_SCHEMA,
            }
        ],
        tool_choice={"type": "tool", "name": _TOOL_NAME},
        messages=[
            {
                "role": "user",
                "content": f"Dictée médicale : {texte_anonymise}",
            }
        ],
    )

    # Extraction du tool_use block — toujours présent grâce à tool_choice forcé
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", "") == _TOOL_NAME:
            return AnalyseClinique(**block.input)

    raise ValueError(
        "Réponse Claude sans tool_use exploitable — extraction sémantique impossible."
    )


def analyser_dictee_dict(dictee: str, *, api_key: str | None = None) -> dict:
    """Wrapper retournant un dict JSON-serialisable (pour Streamlit session_state)."""
    result = analyser_dictee(dictee, api_key=api_key)
    return result.model_dump()
