"""
clinical/next_action.py — Moteur "Next-Best-Action" pour l'IAO.

Donne à l'IAO la prochaine action prioritaire selon l'état clinique courant.
Pure function, sans dépendance Streamlit, donc testable et déterministe.

Arbre de décision priorisé (du plus critique au moins) :
  1. Vitaux invalides             → corriger
  2. Vitaux manquants             → saisir
  3. NEWS2 ≥ 7 sans triage        → triage immédiat
  4. AVC suspect fenêtre ouverte  → code stroke
  5. qSOFA ≥ 2 + fièvre           → sepsis bundle 1h
  6. NEWS2 ≥ 5 sans triage        → valider triage
  7. AOD + traumatisme            → pharmacie antidote
  8. Triage P1/M sans SBAR        → SBAR pour appel équipe
  9. Délai triage dépassé         → escalade médicale
 10. Triage stable > 30 min       → réévaluation due
 11. EVA ≥ 7 sans antalgie        → initier antalgie
 12. Triage P3-P5 + réadmission   → ré-examen médical
 13. État OK                      → bilan / surveillance

Chaque règle retourne un dict NextAction.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional


# Niveaux d'urgence (impacts couleur/icône UI)
URGENCY_CRITICAL = "critical"   # action vitale, < 1 min
URGENCY_HIGH     = "high"       # action urgente, < 5 min
URGENCY_MEDIUM   = "medium"     # action à planifier, < 30 min
URGENCY_LOW      = "low"        # action de fond
URGENCY_DONE     = "done"       # tout est OK


@dataclass
class NextAction:
    label:         str             # Texte principal affiché
    detail:        str             # Explication courte (1 phrase)
    urgency:       str             # critical | high | medium | low | done
    target_tabs:   Optional[str]   # "Triage" ou "Suivi|SBAR" pour bottom nav
    target_anchor: Optional[str]   # ID HTML pour scroll
    source:        str             # Source clinique (RCP, SFMU…)
    icon:          str = "🎯"

    def to_dict(self) -> dict:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────────────
# RÈGLES — Ordre = priorité (la première qui matche gagne)
# ──────────────────────────────────────────────────────────────────────────────

def _vitaux_invalides(state: dict) -> Optional[NextAction]:
    """NEWS2 a échoué → vitaux corrompus."""
    if state.get("news2_error"):
        return NextAction(
            label="Corriger les vitaux invalides",
            detail=f"NEWS2 indisponible : {state.get('news2_error', '')[:80]}",
            urgency=URGENCY_CRITICAL,
            target_tabs="Triage",
            target_anchor="akir-anchor-vitaux",
            source="Sécurité saisie",
            icon="⚠️",
        )
    return None


def _vitaux_manquants(state: dict) -> Optional[NextAction]:
    """Pas encore de vitaux complets saisis."""
    fc, pas, spo2, fr = state.get("fc"), state.get("pas"), state.get("spo2"), state.get("fr")
    if not all([fc, pas, spo2, fr]):
        return NextAction(
            label="Saisir les constantes vitales",
            detail="Au moins FC, PAS, SpO2, FR sont nécessaires pour calculer NEWS2.",
            urgency=URGENCY_HIGH,
            target_tabs="Triage",
            target_anchor="akir-anchor-vitaux",
            source="NEWS2 — RCP 2017",
            icon="📊",
        )
    return None


def _news2_critique_sans_triage(state: dict) -> Optional[NextAction]:
    """NEWS2 ≥ 7 sans triage validé → triage immédiat."""
    n2 = state.get("news2")
    if n2 is not None and n2 >= 7 and not state.get("triage_validated"):
        return NextAction(
            label=f"URGENCE — Valider Tri M/1 (NEWS2 {n2})",
            detail="Engagement vital — déchocage immédiat — appel médical sans délai.",
            urgency=URGENCY_CRITICAL,
            target_tabs="Triage",
            target_anchor="akir-anchor-triage",
            source="NEWS2 ≥ 7 — RCP 2017",
            icon="🚨",
        )
    return None


def _stroke_fenetre_ouverte(state: dict) -> Optional[NextAction]:
    """AVC suspect avec délai début symptômes < 4.5h."""
    if state.get("avc_suspect") and state.get("avc_delai_h") is not None:
        delai = float(state["avc_delai_h"])
        if delai <= 4.5:
            return NextAction(
                label=f"Code Stroke — TDM cérébral URGENT (délai {delai:.1f}h)",
                detail="Fenêtre thrombolyse ouverte. Door-to-needle ≤ 60 min.",
                urgency=URGENCY_CRITICAL,
                target_tabs="Triage",
                target_anchor="akir-anchor-triage",
                source="ESO 2023 / SFMU FRENCH",
                icon="🧠",
            )
    return None


def _sepsis_bundle(state: dict) -> Optional[NextAction]:
    """qSOFA ≥ 2 + fièvre ≥ 38°C → bundle sepsis 1h."""
    qsofa = state.get("qsofa", 0)
    temp  = state.get("temp")
    if qsofa >= 2 and temp is not None and temp >= 38.0:
        return NextAction(
            label="Sepsis suspecté — Bundle 1h",
            detail="Lactates + 2 hémocultures + antibiothérapie probabiliste < 1h.",
            urgency=URGENCY_CRITICAL,
            target_tabs="Triage",
            target_anchor="akir-anchor-triage",
            source="Surviving Sepsis Campaign 2021",
            icon="🦠",
        )
    return None


def _news2_eleve_sans_triage(state: dict) -> Optional[NextAction]:
    """NEWS2 5-6 sans triage validé."""
    n2 = state.get("news2")
    if n2 is not None and n2 >= 5 and not state.get("triage_validated"):
        return NextAction(
            label=f"Valider le triage (NEWS2 {n2})",
            detail="Risque élevé — appel médical < 30 min recommandé.",
            urgency=URGENCY_HIGH,
            target_tabs="Triage",
            target_anchor="akir-anchor-triage",
            source="NEWS2 ≥ 5 — RCP 2017",
            icon="⚡",
        )
    return None


def _aod_trauma(state: dict) -> Optional[NextAction]:
    """Anticoagulant + traumatisme → antidote prêt."""
    if state.get("aod_or_avk") and state.get("trauma"):
        return NextAction(
            label="Préparer antidote anticoagulant",
            detail="Dabigatran → Idarucizumab 5 g IV. Xa-inh → Andexanet. AVK → PPSB + Vit K.",
            urgency=URGENCY_HIGH,
            target_tabs="Triage",
            target_anchor="akir-anchor-triage",
            source="SFMU 2023 — AOD reversal",
            icon="💉",
        )
    return None


def _p1_sans_sbar(state: dict) -> Optional[NextAction]:
    """Triage P1/M validé mais SBAR pas encore généré."""
    niv = state.get("triage_level")
    if niv in ("M", "1") and not state.get("sbar_generated"):
        return NextAction(
            label="Générer SBAR pour appel équipe",
            detail=f"Tri {niv} — transmettre situation/background/assessment/recommendation.",
            urgency=URGENCY_HIGH,
            target_tabs="Suivi|SBAR",
            target_anchor="akir-anchor-sbar",
            source="ISBAR — JCI",
            icon="📡",
        )
    return None


def _delai_triage_depasse(state: dict) -> Optional[NextAction]:
    """Délai cible du niveau de triage dépassé."""
    elapsed_min = state.get("triage_elapsed_min", 0)
    niv = state.get("triage_level")
    delais = {"M": 5, "1": 5, "2": 15, "3A": 30, "3B": 60, "4": 120}
    cible = delais.get(niv)
    if cible and elapsed_min > cible:
        return NextAction(
            label=f"DÉLAI TRI {niv} DÉPASSÉ ({elapsed_min:.0f} min)",
            detail=f"Cible {cible} min. Escalade médicale immédiate.",
            urgency=URGENCY_CRITICAL,
            target_tabs="Suivi|Réévaluation",
            target_anchor="akir-anchor-reev",
            source="FRENCH V1.1 — Délais cibles",
            icon="⏱️",
        )
    return None


def _reevaluation_due(state: dict) -> Optional[NextAction]:
    """Triage validé > 30 min sans réévaluation."""
    elapsed = state.get("last_reev_min")
    if elapsed is not None and elapsed >= 30 and state.get("triage_validated"):
        return NextAction(
            label=f"Réévaluation due ({elapsed:.0f} min sans contrôle)",
            detail="Refaire vitaux + delta NEWS2. Aggravation = appel médical.",
            urgency=URGENCY_MEDIUM,
            target_tabs="Suivi|Réévaluation",
            target_anchor="akir-anchor-reev",
            source="HAS — Réévaluation IAO",
            icon="🔄",
        )
    return None


def _eva_eleve_sans_antalgie(state: dict) -> Optional[NextAction]:
    """EVA ≥ 7 et pas d'antalgie initiée."""
    eva = state.get("eva", 0)
    if eva >= 7 and not state.get("antalgie_initiee"):
        return NextAction(
            label=f"Antalgie palier 3 (EVA {eva}/10)",
            detail="Douleur sévère non contrôlée — morphine titrée ou kétamine IN selon protocole.",
            urgency=URGENCY_MEDIUM,
            target_tabs="Triage",
            target_anchor="akir-anchor-triage",
            source="OMS palier antalgique",
            icon="💊",
        )
    return None


def _readmission_elevee_sous_triage(state: dict) -> Optional[NextAction]:
    """Risque réadmission élevé + triage non-urgent → discussion équipe."""
    if state.get("readmission_risk") == "Élevé" and state.get("triage_level") in ("3B", "4", "5"):
        return NextAction(
            label="Réadmission probable malgré triage faible",
            detail="Score LACE élevé + triage non-urgent : discussion médicale recommandée.",
            urgency=URGENCY_MEDIUM,
            target_tabs="Triage",
            target_anchor="akir-anchor-triage",
            source="LACE — Walraven 2010",
            icon="🔁",
        )
    return None


def _patient_stable(state: dict) -> NextAction:
    """Aucune règle déclenchée → patient stable."""
    if state.get("triage_validated"):
        return NextAction(
            label="Patient stable — surveillance",
            detail="Triage validé, NEWS2 bas, pas de drapeau rouge. Réévaluation à 30 min.",
            urgency=URGENCY_DONE,
            target_tabs="Suivi|Réévaluation",
            target_anchor="akir-anchor-reev",
            source="HAS — Surveillance IAO",
            icon="✅",
        )
    return NextAction(
        label="Compléter l'évaluation initiale",
        detail="Continuer à renseigner motif et discriminants pour valider le triage.",
        urgency=URGENCY_LOW,
        target_tabs="Triage",
        target_anchor="akir-anchor-triage",
        source="FRENCH V1.1",
        icon="📝",
    )


# Ordre = priorité (premier match gagne)
_RULES = [
    _vitaux_invalides,
    _vitaux_manquants,
    _news2_critique_sans_triage,
    _stroke_fenetre_ouverte,
    _sepsis_bundle,
    _news2_eleve_sans_triage,
    _aod_trauma,
    _p1_sans_sbar,
    _delai_triage_depasse,
    _reevaluation_due,
    _eva_eleve_sans_antalgie,
    _readmission_elevee_sous_triage,
]


# ──────────────────────────────────────────────────────────────────────────────
# API publique
# ──────────────────────────────────────────────────────────────────────────────

def compute_next_action(state: dict) -> NextAction:
    """
    Évalue toutes les règles dans l'ordre de priorité et retourne la première
    qui matche. Si aucune règle ne déclenche, retourne un message de stabilité.

    Args:
        state: dict contenant l'état clinique courant. Clés attendues (toutes
               optionnelles) :
            fc, pas, spo2, fr, temp, gcs : vitaux numériques
            news2 : int | None (None si erreur de calcul)
            news2_error : str | None (message d'erreur si vitaux invalides)
            qsofa : int (0-3)
            eva : int (0-10)
            triage_validated : bool
            triage_level : "M"|"1"|"2"|"3A"|"3B"|"4"|"5"|None
            triage_elapsed_min : float (minutes depuis triage validé)
            last_reev_min : float (minutes depuis dernière réévaluation)
            sbar_generated : bool
            antalgie_initiee : bool
            aod_or_avk : bool
            trauma : bool
            avc_suspect : bool
            avc_delai_h : float | None
            readmission_risk : "Faible"|"Modéré"|"Élevé"|None

    Returns:
        NextAction toujours non-None (fallback "stable" ou "compléter").
    """
    for rule in _RULES:
        action = rule(state)
        if action is not None:
            return action
    return _patient_stable(state)


# Couleurs CSS par niveau d'urgence (alignées sur le code couleur triage)
URGENCY_STYLE = {
    URGENCY_CRITICAL: {"bg": "#7C3AED", "color": "#fff",    "border": "#5B21B6"},
    URGENCY_HIGH:     {"bg": "#EF4444", "color": "#fff",    "border": "#B91C1C"},
    URGENCY_MEDIUM:   {"bg": "#F59E0B", "color": "#fff",    "border": "#B45309"},
    URGENCY_LOW:      {"bg": "#3B82F6", "color": "#fff",    "border": "#1D4ED8"},
    URGENCY_DONE:     {"bg": "#22C55E", "color": "#fff",    "border": "#15803D"},
}
