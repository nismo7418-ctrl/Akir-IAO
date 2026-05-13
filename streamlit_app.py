# streamlit_app.py — AKIR-IAO v20 — Système Expert Grade Hospitalier
# Développeur : Ismail Ibn-Daifa — Hainaut, Wallonie, Belgique
# UX refonte : "One-screen workflow" — confort IAO urgences — Mobile-first

import streamlit as st
import uuid, io, csv as csv_mod, traceback
from datetime import datetime
import joblib
import numpy as np

st.set_page_config(
    page_title="AKIR-IAO v20",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── PWA / iOS / Android meta — comportement app + safe-area ──────────────────
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="AKIR-IAO">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#004A99">
<meta name="format-detection" content="telephone=no">
""", unsafe_allow_html=True)

from config import *
from clinical.news2 import (
    calculer_news2, n2_meta,
    pews_meta, seuils_normaux_ped,
    calculer_pews as calculer_pews_vitaux,
)
from clinical.triage import french_triage, verifier_coherence
from clinical.scores import (
    calculer_gcs, calculer_qsofa, calculer_heart,
    calculer_timi, evaluer_fast, calculer_algoplus, evaluer_cfs,
    calculer_wells_tvp, calculer_wells_ep, calculer_nihss,
    calculer_sofa_partiel, calculer_curb65,
    regle_ottawa_cheville, regle_canadian_ct,
    calculer_abcd2, calculer_perc, calculer_grace,
    calculer_ciwa, calculer_pews,
    calculer_nihss_rapide, calculer_pram,
    calculer_croup, poids_estime_enfant,
    surface_corporelle_mosteller, terme_naegele,
    calculer_pss, identifier_toxidrome, evaluer_paracetamol_intox,
    evaluer_tricycliques_ecg, calculer_toxic2,
    TOXIDROMES, PSS_CRITERES,
)
from clinical.vitaux import si, sipa
from clinical.perfusion import (
    perf_morphine, perf_piritramide, perf_ketamine,
    perf_midazolam, perf_adrenaline, perf_noradrenaline,
    perf_insuline, perf_amiodarone, perf_labetalol,
    perf_magnesium, perf_nicardipine, perf_dobutamine,
    calculer_debit, convertir_debit,
)
from clinical.pharmaco import (
    paracetamol, naproxene, ketorolac, diclofenac, tramadol, piritramide, morphine,
    naloxone, adrenaline, glucose, ceftriaxone, litican,
    salbutamol, furosemide, ondansetron, acide_tranexamique,
    methylprednisolone, crise_hypertensive, neutralisation_aod,
    sepsis_bundle_1h, ketamine_intranasale, vesiera,
    protocole_eva, protocole_epilepsie_ped,
    taradyl_im, diclofenac_im,
    clevidipine, meopa, midazolam_iv,
    poids_ideal_theorique, poids_dosage_opioides,
    midazolam_im, PROTOCOLES_IAO, check_safety, generer_etiquette,
)
from clinical.french_v12 import (
    FRENCH_MOTS_CAT, FRENCH_MOTIFS_RAPIDES,
    get_protocol, render_discriminants, apply_discriminant_selection,
    DISCRIMINANTS_ENRICHIS, render_discriminants_enrichis, process_answers,
)
from ui.eva_pqrst import (
    EVA_WIDGET_COMPLET, SCHEMA_BRULURES, QUESTIONS_AVANCEES,
    CHECKLIST_5B, COURBE_VITAUX, PRESCRIPTIONS_ANTICIPEES,
)
# clinical/mug.py retiré (dead code — onglet MUG abandonné)
from clinical.tools import (
    calculer_rsi, calculer_recharge_volemique, broselow,
    convertir_opioides, corriger_natrémie, calculer_dfge,
    code_stroke_delais, joules_defibrillateur, calculer_blatchford,
    RSI_AGENTS, CURARES_RSI, OPIOIDES_RATIO_IV,
)
from persistence.registry import enregistrer_patient, charger_registre
from akir_iao_enhancements import (
    inject_mobile_first_css,
    sync_clinical_context,
    gcs_visual_scale, borg_visual_scale, cam_icu_visual,
    section_dilutions_hainaut, calculateur_noradrenaline,
    section_fiches_medicaments,
)
from persistence.audit import audit_verifier_integrite
from ui.styles import load_css
from ui.components import (
    H, SEC, AL, CARD, CARD_END, PURPURA, N2_BANNER,
    GAUGE, VITAUX, TRI_CARD_INLINE, TRI_BANNER_FIXED,
    RX, RX_LOCK, GLYC_WIDGET, BPCO_WIDGET, SI_WIDGET,
    SBAR_RENDER, DISC, build_sbar, EVA_BAR,
)
from ui.triage_tab import (
    apply_new_triage_reset_to_session,
    apply_voice_triage_to_session,
    render as render_triage,
)
from ui.pharmacie_tab import render as render_pharmacie
from ui.scores_tab import render as render_scores
from ui.readmission_tab import render as render_readmission
from ui.mortality_tab import render as render_mortality
from clinical.next_action import compute_next_action, URGENCY_STYLE, URGENCY_DONE
from clinical.prefill import (
    build_triage_payload, build_mortality_payload, build_readmission_prefill,
    gcs_to_avpu, motif_is_trauma,
)
from ui.explainer import explain, glossary_grid, info_chip

MOTS_CAT       = FRENCH_MOTS_CAT
MOTIFS_RAPIDES = FRENCH_MOTIFS_RAPIDES

# ── Chargement du modèle IA ───────────────────────────────────────────────────
@st.cache_resource
def load_triage_model():
    try:
        return joblib.load("triage_model.joblib")
    except FileNotFoundError:
        st.error("Modèle IA introuvable. Lancez d'abord `python train_IA.py`.")
        return None

# ── Session State ─────────────────────────────────────────────────────────────
SS = st.session_state
_defaults = {
    "op": "", "sid": str(uuid.uuid4())[:8].upper(), "uid": None,
    "t_arr": None, "t_cont": None, "t_reev": None,
    "v_temp": 37.0, "v_fc": 80, "v_pas": 120,
    "v_spo2": 98, "v_fr": 16, "v_gcs": 15,
    "gcs_y": 4, "gcs_v": 5, "gcs_m": 6,
    "v_news2": 0, "v_bpco": False,
    "age": 45, "age_mois": 3, "poids": 70, "taille": 170,
    "alg": "", "o2": False, "atcd_other": [],
    "motif": "", "cat": "", "eva": 0, "gl": None,
    "niv": None, "just": "", "crit": "",
    "det": {}, "uid_cur": None,
    "histo": [], "reevs": [],
    "timers": {},  # {"nom": datetime}
    "atcd": [], "atcd_checks": {}, "risk_checks": {}, "trt_checks": {},
    "tab_active": 0,
}
for _k, _v in _defaults.items():
    if _k not in SS:
        SS[_k] = _v
if not SS.get("uid"):
    SS.uid = SS.sid

load_css()

# ── Helpers locaux ────────────────────────────────────────────────────────────
def WK(base: str, scope: str | None = None) -> str:
    parts = [str(SS.get("uid") or SS.get("sid") or "s")]
    if scope:
        parts.append(str(scope))
    parts.append(str(base))
    return "__".join(p.replace(" ", "_") for p in parts if p)

@st.cache_data(show_spinner=False, max_entries=200)
def _calc_news2(fr, spo2, o2, temp, pas, fc, gcs, bpco):
    """Pure wrapper cacheable. Lève ValueError sur vitaux invalides."""
    n2, _ = calculer_news2(fr, spo2, o2, temp, pas, fc, gcs, bpco)
    return n2

def _n2() -> int | None:
    """Retourne le NEWS2 courant ou None si les vitaux sont invalides.
    L'erreur est affichée à l'écran — pas de fallback silencieux à 0.
    """
    sync_clinical_context(SS)
    try:
        n2 = _calc_news2(
            SS.v_fr, SS.v_spo2, SS.o2,
            SS.v_temp, SS.v_pas, SS.v_fc, SS.v_gcs, SS.v_bpco)
        SS.v_news2 = n2
        return n2
    except ValueError as exc:
        st.error(f"🚨 NEWS2 indisponible — {exc}")
        SS.v_news2 = None
        return None

apply_new_triage_reset_to_session(SS, WK)
apply_voice_triage_to_session(SS, WK)

# Variables patient depuis SS
age         = float(SS.get("age") or 45)
poids       = float(SS.get("poids") or 70)
taille      = float(SS.get("taille") or 170)
atcd        = list(SS.get("atcd") or [])
alg         = str(SS.get("alg") or "")
o2          = bool(SS.get("o2") or False)
atcd_checks = dict(SS.get("atcd_checks") or {})
risk_checks = dict(SS.get("risk_checks") or {})
trt_checks  = dict(SS.get("trt_checks") or {})
smart_context = sync_clinical_context(SS)

# ── CSS additionnel inline UX ─────────────────────────────────────────────────
H("""<style>
/* ── Barre sticky de statut patient ─────────────────────────────────── */
.sticky-bar {
  position: sticky; top: 0; z-index: 100;
  background: var(--CARD);
  border-bottom: 2px solid var(--B);
  padding: 6px 14px;
  display: flex; align-items: center; gap: 10px;
  margin: -4px -1rem 10px;
  box-shadow: var(--s1);
}
.sticky-badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px; border-radius: 20px;
  font-size: .68rem; font-weight: 700; font-family: 'IBM Plex Mono', monospace;
  border: 1.5px solid currentColor; white-space: nowrap;
}
.badge-age   { color: #2563EB; border-color: #BFDBFE; background: #EFF6FF; }
.badge-poids { color: #7C3AED; border-color: #DDD6FE; background: #F5F3FF; }
.badge-atcd  { color: #B45309; border-color: #FDE68A; background: #FFFBEB; }
.badge-triage { font-size: .72rem; font-weight: 800; padding: 4px 12px; }
.badge-chrono { color: var(--TM); font-family: 'IBM Plex Mono', monospace; font-size: .8rem; margin-left:auto; }

/* ── Boutons d'action rapide des vitaux ─────────────────────────────── */
.vbtn-grid {
  display: grid; grid-template-columns: repeat(4,1fr); gap: 6px; margin: 8px 0;
}
.vbtn {
  background: var(--BG2); border: 1.5px solid var(--B);
  border-radius: var(--r2); padding: 6px 4px;
  text-align: center; cursor: pointer; transition: all .12s;
  font-size: .7rem; font-weight: 600; color: var(--T);
}
.vbtn:hover, .vbtn.active {
  border-color: var(--P); background: var(--PP); color: var(--P);
}
.vbtn .vbtn-val { font-size: 1rem; font-family: 'IBM Plex Mono', monospace; }
.vbtn .vbtn-lbl { font-size: .6rem; color: var(--TM); }

/* ── Carte de triage proéminente ────────────────────────────────────── */
.tri-hero {
  border-radius: 14px; padding: 20px 18px; text-align: center;
  box-shadow: var(--s3); margin: 12px 0;
}
.tri-hero-level { font-size: 2rem; font-weight: 900; letter-spacing: -.03em; }
.tri-hero-just  { font-size: .82rem; margin-top: 6px; opacity: .9; line-height: 1.5; }
.tri-hero-meta  {
  display: flex; gap: 10px; justify-content: center; margin-top: 10px; flex-wrap: wrap;
}
.tri-meta-chip {
  background: rgba(255,255,255,.18); padding: 3px 10px; border-radius: 12px;
  font-size: .65rem; font-family: 'IBM Plex Mono', monospace;
}

/* ── Score NEWS2 en ligne avec les vitaux ───────────────────────────── */
.news2-inline {
  display: flex; align-items: center; gap: 8px; margin: 6px 0;
  padding: 8px 12px; background: var(--BG2); border-radius: var(--r2);
  border: 1.5px solid var(--B);
}
.news2-number {
  font-size: 2rem; font-weight: 900; font-family: 'IBM Plex Mono', monospace;
  min-width: 2.5ch; text-align: center;
}
.news2-label { font-size: .72rem; color: var(--TM); line-height: 1.3; }
.news2-risk  { font-size: .7rem; font-weight: 700; }

/* ── Timer urgent ────────────────────────────────────────────────────── */
.timer-widget {
  background: var(--T); color: var(--TW);
  border-radius: var(--r); padding: 10px 14px;
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
}
.timer-digits {
  font-family: 'IBM Plex Mono', monospace; font-size: 1.8rem; font-weight: 700;
}
.timer-label { font-size: .62rem; opacity: .6; text-transform: uppercase; letter-spacing: .1em; }

/* ── EVA large et tactile ────────────────────────────────────────────── */
.eva-hero {
  display: grid; grid-template-columns: repeat(11,1fr); gap: 4px; margin: 8px 0;
}
.eva-btn {
  padding: 10px 2px; border-radius: 8px; text-align: center;
  font-size: .85rem; font-weight: 700; cursor: pointer; transition: transform .1s;
  min-height: 46px; display: flex; align-items: center; justify-content: center;
}
.eva-btn.active { transform: scale(1.08); box-shadow: 0 0 0 3px rgba(0,0,0,.25); }

/* ── Pharmacie : carte compacte ─────────────────────────────────────── */
.rx-compact {
  border-left: 4px solid var(--P); border-radius: 0 var(--r2) var(--r2) 0;
  padding: 10px 14px; background: var(--BG2); margin: 6px 0;
  display: flex; align-items: flex-start; gap: 12px;
}
.rx-compact-dose {
  font-size: 1.1rem; font-weight: 800; font-family: 'IBM Plex Mono', monospace;
  color: var(--P); white-space: nowrap; min-width: 80px;
}
.rx-compact-info { flex: 1; }
.rx-compact-name { font-size: .82rem; font-weight: 600; }
.rx-compact-detail { font-size: .72rem; color: var(--TM); margin-top: 2px; }

/* ── Pharmacie urgence = rouge ──────────────────────────────────────── */
.rx-compact.urgent { border-color: var(--ERR); }
.rx-compact.urgent .rx-compact-dose { color: var(--ERR); }

/* ── Grille vitaux condensée  ───────────────────────────────────────── */
.vg6 {
  display: grid; grid-template-columns: repeat(3,1fr);
  gap: 6px; margin: 8px 0;
}
@media (min-width: 480px) { .vg6 { grid-template-columns: repeat(6,1fr); } }
.vbox {
  background: var(--CARD); border: 1.5px solid var(--B);
  border-radius: var(--r2); padding: 8px 6px; text-align: center;
}
.vbox.crit { border-color: var(--ERR); background: var(--ERR-bg); }
.vbox.warn { border-color: var(--WRN); background: var(--WRN-bg); }
.vbox-lbl { font-size: .58rem; color: var(--TM); text-transform: uppercase; letter-spacing: .06em; }
.vbox-val { font-size: 1.15rem; font-weight: 800; font-family: 'IBM Plex Mono', monospace; }

/* ── Alerte pharmacovigilance sticky bas ────────────────────────────── */
.pharma-alert-bar {
  background: #7F1D1D; color: #FEE2E2;
  border-radius: var(--r2); padding: 8px 14px;
  font-size: .75rem; font-weight: 700; margin: 6px 0;
}

/* ── Onglets mobiles plus grands ────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap: 2px; }
.stTabs [data-baseweb="tab"] {
  padding: 10px 8px !important; font-size: .72rem !important;
  min-width: 0 !important; font-weight: 600 !important;
}

/* ── Sidebar minimale ───────────────────────────────────────────────── */
@media (max-width: 768px) {
  [data-testid="stSidebar"],
  [data-testid="collapsedControl"] { display: none !important; }
  .block-container { padding: .4rem .5rem max(4rem, env(safe-area-inset-bottom, 1rem)) !important; }
  button, .stButton > button { min-height: 48px !important; font-weight: 700 !important; }
}

/* ══════════════════════════════════════════════════════════════════
   MOBILE-OPTIMIZATION — Safe area iOS + tactile renforcé
══════════════════════════════════════════════════════════════════ */
@supports (padding: max(0px)) {
  .block-container {
    padding-left:  max(.875rem, env(safe-area-inset-left))  !important;
    padding-right: max(.875rem, env(safe-area-inset-right)) !important;
  }
  .sticky-bar { padding-top: max(6px, env(safe-area-inset-top, 0px)); }
}

/* ── Sticky bar scrollable horizontalement sur mobile ──────────────── */
@media (max-width: 768px) {
  .sticky-bar {
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch;
    scroll-snap-type: x proximity;
    padding: 6px 8px !important;
    gap: 6px !important;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }
  .sticky-bar::-webkit-scrollbar { display: none; }
  .sticky-bar .sticky-badge {
    flex-shrink: 0;
    scroll-snap-align: start;
    padding: 4px 8px !important;
    font-size: .65rem !important;
  }
  .sticky-bar .badge-chrono {
    position: sticky; right: 0;
    background: var(--CARD);
    padding-left: 6px;
    box-shadow: -6px 0 8px -4px rgba(0,0,0,.15);
  }
}

/* ── Onglets : compact emoji-first sous 480px ──────────────────────── */
@media (max-width: 480px) {
  .stTabs [data-baseweb="tab-list"] {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scroll-snap-type: x mandatory;
    scrollbar-width: none;
  }
  .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
  .stTabs [data-baseweb="tab"] {
    flex: 0 0 auto !important;
    scroll-snap-align: start;
    padding: 12px 10px !important;
    min-width: 64px !important;
    font-size: .68rem !important;
  }
  /* Le tab actif s'élargit pour montrer le label complet */
  .stTabs [data-baseweb="tab"][aria-selected="true"] {
    min-width: 110px !important;
    font-size: .72rem !important;
  }
}

/* ── Inputs : empêcher le zoom iOS sur focus (font-size ≥ 16px) ────── */
@media (max-width: 768px) {
  input[type="text"],
  input[type="number"],
  input[type="tel"],
  input[type="email"],
  textarea,
  [data-baseweb="select"] input,
  .stNumberInput input,
  .stTextInput input,
  .stTextArea textarea {
    font-size: 16px !important;
  }
  /* Tap targets agrandis pour boutons +/- des number inputs */
  .stNumberInput button,
  .stNumberInput [role="button"] {
    min-width: 36px !important;
    min-height: 36px !important;
  }
  /* Selectbox plus haut pour le tactile */
  [data-baseweb="select"] > div { min-height: 44px !important; }
}

/* ── Tabs : retirer le scroll-snap quand desktop ───────────────────── */
@media (min-width: 481px) {
  .stTabs [data-baseweb="tab-list"] { scroll-snap-type: none; }
}

/* ── Chips de presets vitaux ───────────────────────────────────────── */
.vp-chips {
  display: flex; gap: 6px; flex-wrap: wrap;
  margin: 6px 0 10px;
}
.vp-chip {
  background: var(--BG2);
  border: 1.5px solid var(--B);
  border-radius: 20px;
  padding: 6px 12px;
  font-size: .72rem;
  font-weight: 600;
  color: var(--TM);
  cursor: pointer;
  transition: all .12s;
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}
.vp-chip:hover, .vp-chip:focus {
  border-color: var(--P);
  background: var(--PP);
  color: var(--P);
}
.vp-chip-danger { border-color: #FCA5A5; color: #B91C1C; background: #FEF2F2; }
.vp-chip-warning { border-color: #FCD34D; color: #B45309; background: #FFFBEB; }
.vp-chip-success { border-color: #86EFAC; color: #166534; background: #F0FDF4; }

@media (max-width: 768px) {
  .vp-chip { padding: 8px 14px; font-size: .78rem; min-height: 42px; }
}

/* ══════════════════════════════════════════════════════════════════
   INFO CHIPS — Explications cliniques accessibles (composant explainer)
════════════════════════════════════════════════════════════════════ */
.akir-info-chip {
  margin: 6px 0;
  border-radius: 8px;
  background: linear-gradient(135deg, #EFF6FF, #F0F9FF);
  border: 1.5px solid #BFDBFE;
  overflow: hidden;
  transition: box-shadow .15s;
}
.akir-info-chip:hover { box-shadow: 0 2px 8px rgba(59,130,246,.15); }
.akir-info-chip > summary {
  cursor: pointer;
  padding: 8px 12px;
  font-size: .76rem;
  font-weight: 600;
  color: #1D4ED8;
  list-style: none;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}
.akir-info-chip > summary::-webkit-details-marker { display: none; }
.akir-info-chip > summary::after {
  content: " ›";
  font-weight: 700;
  transition: transform .15s;
  display: inline-block;
}
.akir-info-chip[open] > summary::after {
  transform: rotate(90deg);
}
.akir-info-body {
  padding: 4px 14px 12px;
  font-size: .78rem;
  line-height: 1.55;
  color: #1E3A8A;
}
.akir-info-body p { margin: 4px 0 8px; }
.akir-info-body strong { color: #1D4ED8; }
.akir-info-source {
  font-size: .68rem !important;
  opacity: .75;
  font-style: italic;
  margin-top: 8px !important;
  border-top: 1px solid #BFDBFE;
  padding-top: 6px;
}

@media (max-width: 480px) {
  .akir-info-chip > summary { padding: 10px 14px; font-size: .82rem; }
  .akir-info-body { font-size: .82rem; padding: 6px 14px 14px; }
}

/* ══════════════════════════════════════════════════════════════════
   NEXT-BEST-ACTION CARD — guide l'IAO vers la prochaine action
════════════════════════════════════════════════════════════════════ */
.next-action-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  margin: 8px 0 12px;
  border-radius: 12px;
  box-shadow: 0 4px 14px rgba(0,0,0,.12);
  transition: opacity .2s;
}
.next-action-card .na-ico {
  font-size: 1.8rem;
  line-height: 1;
  flex-shrink: 0;
}
.next-action-card .na-body {
  flex: 1;
  min-width: 0;
}
.next-action-card .na-label {
  font-size: .95rem;
  font-weight: 800;
  line-height: 1.25;
  letter-spacing: .01em;
}
.next-action-card .na-detail {
  font-size: .74rem;
  opacity: .92;
  margin-top: 3px;
  line-height: 1.4;
}
.next-action-card .na-source {
  font-size: .62rem;
  opacity: .68;
  margin-top: 4px;
  font-family: 'IBM Plex Mono', monospace;
  letter-spacing: .03em;
  text-transform: uppercase;
}
.next-action-card .na-cta {
  background: rgba(255,255,255,.18);
  border: 1.5px solid rgba(255,255,255,.32);
  color: inherit;
  width: 44px; height: 44px;
  border-radius: 50%;
  font-size: 1.3rem;
  font-weight: 800;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform .12s, background .12s;
  -webkit-tap-highlight-color: transparent;
}
.next-action-card .na-cta:hover,
.next-action-card .na-cta:active {
  background: rgba(255,255,255,.32);
  transform: scale(1.06);
}

@media (max-width: 480px) {
  .next-action-card { padding: 10px 12px; gap: 10px; }
  .next-action-card .na-ico { font-size: 1.5rem; }
  .next-action-card .na-label { font-size: .86rem; }
  .next-action-card .na-detail { font-size: .68rem; }
  .next-action-card .na-source { font-size: .58rem; }
  .next-action-card .na-cta { width: 40px; height: 40px; }
}

/* ══════════════════════════════════════════════════════════════════
   BOTTOM NAV MOBILE — 4 actions principales toujours accessibles
   Visible uniquement < 768px. Switch tab + scroll via JS.
══════════════════════════════════════════════════════════════════ */
.bottom-nav { display: none; }

@media (max-width: 768px) {
  .bottom-nav {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: var(--CARD);
    border-top: 1.5px solid var(--B);
    padding-top: 6px;
    padding-bottom: calc(6px + env(safe-area-inset-bottom, 0px));
    padding-left:   calc(8px + env(safe-area-inset-left, 0px));
    padding-right:  calc(8px + env(safe-area-inset-right, 0px));
    display: flex;
    justify-content: space-around;
    align-items: center;
    z-index: 9999;
    box-shadow: 0 -2px 12px rgba(0,0,0,.10);
  }
  .bnav-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    padding: 6px 4px;
    text-decoration: none;
    color: var(--TM);
    transition: color .15s, background .12s, transform .08s;
    min-height: 52px;
    border-radius: 10px;
    cursor: pointer;
    border: none;
    background: transparent;
    -webkit-tap-highlight-color: transparent;
    user-select: none;
  }
  .bnav-btn:active {
    background: var(--P12);
    color: var(--P);
    transform: scale(0.96);
  }
  .bnav-btn.active {
    color: var(--P);
  }
  .bnav-btn.active .bnav-ico {
    transform: scale(1.10);
  }
  .bnav-ico {
    font-size: 1.45rem;
    line-height: 1;
    transition: transform .15s;
  }
  .bnav-lbl {
    font-size: .64rem;
    margin-top: 3px;
    font-weight: 700;
    letter-spacing: .02em;
    text-transform: uppercase;
  }
  /* Bottom-padding sur le contenu pour ne pas être masqué par la nav */
  .block-container {
    padding-bottom: calc(5rem + env(safe-area-inset-bottom, 0px)) !important;
  }
}

/* ── Texte sélectionnable désactivé sur boutons mobiles ────────────── */
@media (max-width: 768px) {
  .stButton > button,
  .vp-chip,
  .sticky-badge {
    -webkit-user-select: none;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
  }
}

</style>""")

inject_mobile_first_css()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Minimaliste (PC) : chrono + reset
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    SEC("AKIR-IAO v20")
    st.caption("Profil patient → onglet 👤 Patient")
    SEC("Chronomètre")
    _sc1, _sc2 = st.columns(2)
    if _sc1.button("⏱ Arrivée", key="sb_arr", use_container_width=True):
        SS.t_arr  = datetime.now()
        SS.histo  = []
        SS.reevs  = []
    if _sc2.button("👨‍⚕️ Contact", key="sb_cont", use_container_width=True):
        SS.t_cont = datetime.now()
    if SS.t_arr:
        _el   = (datetime.now() - SS.t_arr).total_seconds()
        _m, _s = divmod(int(_el), 60)
        _col  = "#EF4444" if _el > 600 else ("#F59E0B" if _el > 300 else "#22C55E")
        H(f'<div style="text-align:center;font-family:monospace;font-size:2rem;font-weight:700;color:{_col};">{_m:02d}:{_s:02d}</div>')
        # Chrono délai cible selon le niveau de triage actif
        if SS.niv and SS.niv in DELAIS:
            _del_sec = DELAIS[SS.niv] * 60
            _reste   = _del_sec - _el
            if _reste > 0:
                _rm, _rs = divmod(int(_reste), 60)
                H(f'<div style="text-align:center;font-size:.72rem;color:#22C55E;font-weight:600;margin-top:2px;">⏱ Délai Tri {SS.niv} : {_rm:02d}:{_rs:02d} restant</div>')
            else:
                _dm, _ds = divmod(int(-_reste), 60)
                H(f'<div style="text-align:center;font-size:.72rem;color:#EF4444;font-weight:800;margin-top:2px;">⚠️ DÉLAI TRI {SS.niv} DÉPASSÉ {_dm:02d}:{_ds:02d}</div>')
    if SS.niv:
        st.divider()
        _css = TCSS.get(SS.niv, "tri-3B")
        H(f'<div class="tri-card {_css}" style="margin:0;padding:8px;border-radius:8px;text-align:center;">'
          f'<div style="font-size:.85rem;font-weight:800;">{LABELS.get(SS.niv,"")} — NEWS2 {SS.v_news2}</div></div>')
    if st.button("🔄 Réinitialiser", use_container_width=True, key="sb_reset"):
        for k, v in _defaults.items():
            SS[k] = v() if callable(v) else v
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# BARRE DE STATUT PATIENT — visible sur tous les onglets
# ─────────────────────────────────────────────────────────────────────────────
def _sticky_bar():
    _smart = sync_clinical_context(SS)
    _age_txt   = f"{int(age)} ans" if age >= 1 else f"{int(age*12)} mois"
    _atcd_n    = len(atcd)
    _niv_txt   = f"TRI {SS.niv}" if SS.niv else "Non trié"
    _niv_css   = TCSS.get(SS.niv, "tri-3B") if SS.niv else ""
    _timer_txt = ""
    if SS.t_arr:
        _el2 = (datetime.now() - SS.t_arr).total_seconds()
        _m2, _s2 = divmod(int(_el2), 60)
        _timer_txt = f"⏱ {_m2:02d}:{_s2:02d}"
    H(f"""<div class="sticky-bar">
      <span class="sticky-badge badge-age">👤 {_age_txt} — {poids:.0f} kg</span>
      {"<span class='sticky-badge badge-atcd'>⚕️ " + str(_atcd_n) + " ATCD</span>" if _atcd_n else ""}
      {"<span class='sticky-badge badge-atcd' style='background:#FEF2F2;color:#991B1B;border-color:#FCA5A5;'>🔴 " + alg + "</span>" if alg else ""}
      <span class="sticky-badge badge-triage {_niv_css}" style="font-size:.72rem;">{_niv_txt}</span>
      {"<span class='sticky-badge' style='color:#92400E;border-color:#F59E0B;background:#FFFBEB;'>⚠️ vitaux/tri</span>" if _smart.get("triage_incoherence") else ""}
      {"<span class='sticky-badge' style='color:#1D4ED8;border-color:#93C5FD;background:#EFF6FF;'>ECG</span>" if _smart.get("ecg_hint") else ""}
      {"<span class='sticky-badge' style='color:#3730A3;border-color:#A5B4FC;background:#EEF2FF;'>NIHSS</span>" if _smart.get("focus_score") == "nihss" else ""}
      {("<span class='sticky-badge' style='color:#38BDF8;border-color:#7DD3FC;background:#EFF6FF;font-size:.72rem;'>" + str(len(SS.reevs)) + " réév.</span>") if SS.reevs else ""}
      {"<span class='sticky-badge' style='color:#EF4444;border-color:#FCA5A5;background:#FEF2F2;'>N2=" + str(SS.v_news2) + "</span>" if (SS.v_news2 is not None and SS.v_news2 >= 5) else ""}
      {"<span class='badge-chrono'>" + _timer_txt + "</span>" if _timer_txt else ""}
    </div>""")


def _render_presentation():
    """Page de présentation intégrée à l'application."""
    H("""<div style="background:linear-gradient(135deg,#0F766E,#2563EB);color:#fff;
      border-radius:12px;padding:18px 20px;margin-bottom:14px;">
      <div style="font-size:.72rem;opacity:.78;text-transform:uppercase;letter-spacing:.12em;">
        Présentation GitHub intégrée
      </div>
      <div style="font-size:1.45rem;font-weight:900;margin-top:2px;">AKIR-IAO v20</div>
      <div style="font-size:.88rem;opacity:.88;margin-top:5px;max-width:820px;">
        Système expert Streamlit d'aide au triage infirmier d'accueil et d'orientation,
        conçu pour structurer rapidement une situation d'urgence.
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;">
        <span class="tag">FRENCH V1.1</span>
        <span class="tag">NEWS2 / PEWS</span>
        <span class="tag">BCFI Belgique</span>
        <span class="tag">SBAR</span>
        <span class="tag">RGPD</span>
      </div>
    </div>""")

    _p1, _p2, _p3, _p4 = st.columns(4)
    _p1.metric("Workflow", "7 onglets")
    _p2.metric("Triage", "M à 5")
    _p3.metric("Suivi", "SBAR")
    _p4.metric("Données", "Anonymes")

    st.markdown(
        """
AKIR-IAO regroupe le profil patient, les constantes vitales, le triage FRENCH,
les scores d'urgence, la pharmacie de première ligne, les outils de réanimation,
la réévaluation et la transmission structurée.
        """
    )

    _c1, _c2 = st.columns(2)
    with _c1:
        H('<div class="card-title">⚡ Triage IAO</div>')
        st.markdown(
            """
- Classification FRENCH V1.1 avec justification clinique.
- NEWS2, PEWS pédiatrique, Shock Index et critères vitaux.
- Discriminants enrichis par motif.
- Pré-remplissage possible par dictée clinique anonymisée.
- Alertes de cohérence entre motif, constantes et niveau proposé.
            """
        )
    with _c2:
        H('<div class="card-title">💊 Pharmacie et sécurité</div>')
        st.markdown(
            """
- Calculs de doses selon poids, âge et contexte.
- Alertes pharmacovigilance : AOD, grossesse, IMAO, insuffisance rénale, allergies.
- Protocoles IAO, perfusions IV, dilutions de réanimation.
- Compatibilité IV en Y et rappel de la règle des 5B.
            """
        )

    _c3, _c4 = st.columns(2)
    with _c3:
        H('<div class="card-title">🧬 Scores et outils</div>')
        st.markdown(
            """
- GCS, qSOFA, HEART, TIMI, NIHSS, ABCD2, Wells, PERC, GRACE, CURB-65.
- Toxicologie : PSS, toxidromes, paracétamol, tricycliques, TOXIC2.
- RSI, Broselow, opioïdes, DFGe, natrémie corrigée, code stroke, défibrillation.
            """
        )
    with _c4:
        H('<div class="card-title">📋 Suivi et traçabilité</div>')
        st.markdown(
            """
- Réévaluations avec delta NEWS2 et courbe des constantes.
- Registre anonymisé limité en taille.
- Export CSV de session.
- Journal d'audit chaîné SHA-256.
- Transmission SBAR générée et téléchargeable.
            """
        )

    st.divider()
    _c5, _c6 = st.columns(2)
    with _c5:
        H('<div class="card-title">📚 Références intégrées</div>')
        st.markdown(
            """
- FRENCH Triage V1.1, SFMU 2018.
- NEWS2, Royal College of Physicians.
- Protocoles et références BCFI/AFMPS pour le contexte belge.
- Scores validés cités dans les modules cliniques.
- Compatibilités IV issues de tableaux HUG.
            """
        )
    with _c6:
        H('<div class="card-title">🤖 Module ML expérimental</div>')
        st.markdown(
            """
Le dépôt contient un classifieur Random Forest de priorité de triage.
Il fournit une aide secondaire à partir des constantes vitales, NEWS2 et AVPU.
Il ne remplace pas le moteur clinique FRENCH.
            """
        )

    st.warning(
        "AKIR-IAO est un outil d'aide à la décision pour professionnels de santé. "
        "Il ne remplace ni le jugement clinique, ni les protocoles institutionnels, "
        "ni les prescriptions médicales."
    )


try:
    # ══ EN-TÊTE COMPACT ══════════════════════════════════════════════════════
    H("""<div class="app-hdr" style="padding:10px 16px;margin-bottom:8px;">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;">
        <div>
          <div class="app-hdr-title" style="font-size:.95rem;">AKIR-IAO v20</div>
          <div class="app-hdr-sub">Triage IAO — Hainaut, Wallonie, Belgique</div>
        </div>
        <div class="app-hdr-tags" style="margin:0;">
          <span class="tag">FRENCH V1.1</span>
          <span class="tag">BCFI</span>
          <span class="tag">RGPD</span>
        </div>
      </div>
    </div>""")

    _sticky_bar()

    # ══ NEXT-BEST-ACTION CARD ════════════════════════════════════════════════
    # Synthèse intelligente : que doit faire l'IAO maintenant ?
    def _build_next_action_state() -> dict:
        """Construit le state pour compute_next_action depuis SS."""
        _atcd_lower = [str(a).lower() for a in (SS.get("atcd") or [])]
        _aod = any(k in " ".join(_atcd_lower) for k in
                   ("anticoagulant", "aod", "avk", "eliquis", "xarelto", "pradaxa", "lixiana"))
        _motif_lower = str(SS.get("motif", "")).lower()
        _trauma = "trauma" in _motif_lower or "chute" in _motif_lower
        _avc_suspect = "avc" in _motif_lower or "déficit" in _motif_lower or SS.get("det", {}).get("avc_suspect", False)
        _avc_delai_h = SS.get("det", {}).get("delai")

        # qSOFA approximatif depuis vitaux
        _fr   = SS.get("v_fr")
        _pas  = SS.get("v_pas")
        _gcs  = SS.get("v_gcs", 15)
        _qsofa = sum([
            (_fr or 0) >= 22,
            (_pas or 200) <= 100,
            (_gcs or 15) < 15,
        ])

        # Minutes depuis le triage / dernière réévaluation
        _now = datetime.now()
        _triage_elapsed = None
        if SS.get("t_arr") and SS.get("niv"):
            _triage_elapsed = (_now - SS.t_arr).total_seconds() / 60
        _last_reev = None
        if SS.get("reevs"):
            try:
                _last_h = SS.reevs[-1].get("h")
                _last_reev = (_now - datetime.fromisoformat(_last_h)).total_seconds() / 60
            except Exception:
                pass

        return {
            "fc":    SS.get("v_fc"),
            "pas":   SS.get("v_pas"),
            "spo2":  SS.get("v_spo2"),
            "fr":    _fr,
            "temp":  SS.get("v_temp"),
            "gcs":   _gcs,
            "news2": SS.get("v_news2"),
            "news2_error": SS.get("v_news2_error"),
            "qsofa": _qsofa,
            "eva":   SS.get("eva", 0),
            "triage_validated":   bool(SS.get("niv")),
            "triage_level":       SS.get("niv"),
            "triage_elapsed_min": _triage_elapsed or 0,
            "last_reev_min":      _last_reev,
            "sbar_generated":     bool(SS.get("sbar_generated")),
            "antalgie_initiee":   bool(SS.get("antalgie_initiee")),
            "aod_or_avk":         _aod,
            "trauma":             _trauma,
            "avc_suspect":        _avc_suspect,
            "avc_delai_h":        _avc_delai_h,
            "readmission_risk":   SS.get("readmission_risk"),
        }

    _na_state  = _build_next_action_state()
    _na        = compute_next_action(_na_state)
    _na_style  = URGENCY_STYLE[_na.urgency]
    _na_dim    = 0.85 if _na.urgency == URGENCY_DONE else 1.0   # apaiser si tout OK
    H(f"""
    <div class="next-action-card" style="
        background:{_na_style['bg']};
        color:{_na_style['color']};
        border-left:5px solid {_na_style['border']};
        opacity:{_na_dim};">
      <div class="na-ico">{_na.icon}</div>
      <div class="na-body">
        <div class="na-label">{_na.label}</div>
        <div class="na-detail">{_na.detail}</div>
        <div class="na-source">{_na.source}</div>
      </div>
      {('<button class="bnav-btn na-cta" data-tabs="' + _na.target_tabs + '" data-anchor="'
        + _na.target_anchor + '" aria-label="Y aller">→</button>')
       if _na.target_tabs and _na.target_anchor else ''}
    </div>
    """)

    # ══ ONGLETS PRINCIPAUX ════════════════════════════════════════════════════
    T = st.tabs([
        "👤 Patient",
        "⚡ Triage",
        "🤖 IA Triage",
        "💊 Pharmacie",
        "🧬 Scores",
        "🛠️ Outils",
        "📋 Suivi",
        "🔄 Réadmission J30",
        "💀 Mortalité ICU",
        "ℹ️ Présentation",
    ])


    # ═══════════════════════════════════════════════════════════════════════════
    # ONGLET 0 — PROFIL PATIENT
    # ═══════════════════════════════════════════════════════════════════════════
    with T[0]:
        H('<div style="background:linear-gradient(135deg,#004A99,#0069D9);color:#fff;border-radius:10px;padding:12px 16px;margin-bottom:12px;">'
          '<div style="font-size:.72rem;opacity:.75;text-transform:uppercase;letter-spacing:.1em;">Renseigner en premier</div>'
          '<div style="font-size:1rem;font-weight:700;">Profil patient</div></div>')

        # Opérateur
        _op = st.text_input("Code opérateur IAO", value=SS.op, max_chars=10, placeholder="IAO01", key="pt_op")
        if _op: SS.op = _op.upper()

        st.divider()

        # ── Biométrie ─────────────────────────────────────────────────────────
        H('<div class="card-title">👤 Biométrie</div>')
        _c1, _c2 = st.columns(2)
        _age_raw = _c1.number_input("Âge (ans)", 0, 120, int(SS.get("age") or 45), key="pt_age")
        _sex = _c2.selectbox("Sexe", ["Non précisé", "Masculin", "Féminin"], key="pt_sex")
        _sex_code = "F" if _sex == "Féminin" else "H"

        if _age_raw == 0:
            _am = st.number_input("Âge en mois", 0, 11, int(SS.get("age_mois") or 3), key="pt_am")
            SS["age_mois"] = _am; SS["age"] = round(_am / 12.0, 4)
            AL(f"Nourrisson de {_am} mois — Seuils pédiatriques actifs", "info")
        else:
            SS["age_mois"] = 0; SS["age"] = float(_age_raw)

        age = float(SS["age"])
        _c3, _c4 = st.columns(2)
        _poids  = _c3.number_input("Poids (kg)", 1, 250, int(SS.get("poids") or 70), key="pt_kg")
        _taille = _c4.number_input("Taille (cm)", 50, 220, int(SS.get("taille") or 170), key="pt_taille")
        SS["poids"] = float(_poids); SS["taille"] = float(_taille)
        poids = SS["poids"]; taille = SS["taille"]

        if taille > 0 and age >= 18:
            imc = round(poids / (taille / 100) ** 2, 1)
            if   imc < 18.5: AL(f"IMC {imc} — Insuffisance pondérale", "warning")
            elif imc < 25.0: st.caption(f"IMC {imc} — Normal")
            elif imc < 30.0: AL(f"IMC {imc} — Surpoids", "info")
            elif imc < 40.0: AL(f"IMC {imc} — Obésité", "warning")
            else:             AL(f"IMC {imc} — Obésité morbide ≥ 40", "danger")
            # Poids idéal théorique (Devine 1974) — important pour dosage opioïdes/BZD
            _pit = poids_ideal_theorique(taille, _sex_code)
            if _pit and imc >= 30:
                _pit_diff = poids - _pit
                H(f'<div style="background:#1E293B;border-radius:6px;padding:6px 12px;margin:4px 0;'
                  f'font-size:.72rem;color:#94A3B8;">'
                  f'💊 Poids idéal (Devine 1974) : <strong style="color:#38BDF8;">{_pit:.0f} kg</strong> '
                  f'(+{_pit_diff:.0f} kg réels) — '
                  f'<strong style="color:#F59E0B;">Doses opioïdes/BZD sur PIT</strong></div>')

        st.divider()

        # ── ATCD — colonnes 2×N (touch-friendly) ──────────────────────────────
        H('<div class="card-title">📋 Antécédents</div>')
        _a1, _a2 = st.columns(2)
        _atcd_checks = {
            "HTA":                            _a1.checkbox("HTA",              key=WK("pt_hta")),
            "Insuffisance cardiaque":         _a2.checkbox("Insuff. cardiaque", key=WK("pt_ic")),
            "Coronaropathie / SCA antérieur": _a1.checkbox("Coronaropathie",   key=WK("pt_coro")),
            "AVC / AIT antérieur":            _a2.checkbox("AVC / AIT",        key=WK("pt_avc")),
            "BPCO":                           _a1.checkbox("BPCO",             key=WK("pt_bpco")),
            "Asthme":                         _a2.checkbox("Asthme",           key=WK("pt_asthme")),
            "Diabète type 2":                 _a1.checkbox("Diabète T2",       key=WK("pt_diab2")),
            "Diabète type 1":                 _a2.checkbox("Diabète T1",       key=WK("pt_diab1")),
            "Insuffisance rénale chronique":  _a1.checkbox("Insuff. rénale",   key=WK("pt_ir")),
            "Insuffisance hépatique":         _a2.checkbox("Insuff. hépatique",key=WK("pt_ih")),
            "Épilepsie":                      _a1.checkbox("Épilepsie",        key=WK("pt_epi")),
            "Fibrillation atriale":           _a2.checkbox("FA",               key=WK("pt_fa")),
            "Drépanocytose":                  _a1.checkbox("Drépanocytose",    key=WK("pt_drep")),
            "Immunodépression":               _a2.checkbox("Immunodépression", key=WK("pt_immuno")),
        }

        H('<div class="card-title" style="margin-top:12px;">⚠️ Facteurs de risque</div>')
        _f1, _f2 = st.columns(2)
        _risk_checks = {
            "Grossesse":                   _f1.checkbox("Grossesse",       key=WK("pt_gros")),
            "Allaitement":                 _f2.checkbox("Allaitement",     key=WK("pt_allait")),
            "Obésité morbide (IMC ≥ 40)": _f1.checkbox("Obésité IMC≥40", key=WK("pt_ob")),
            "Chirurgie récente (<4 sem.)": _f2.checkbox("Chir. récente",   key=WK("pt_chir")),
            "Tabagisme":                   _f1.checkbox("Tabagisme",       key=WK("pt_tabac")),
        }
        if _risk_checks.get("Grossesse"):
            _trim = st.selectbox("Trimestre", ["T1 (< 14 SA)", "T2 (14-28 SA)", "T3 (> 28 SA)"], key="pt_trim")
            AL(f"Grossesse {_trim} — Adapter les thérapeutiques", "warning")

        H('<div class="card-title" style="margin-top:12px;">💊 Traitements</div>')
        _t1, _t2 = st.columns(2)
        _trt_checks = {
            "Anticoagulants/AOD":          _t1.checkbox("Anticoagulants",  key=WK("pt_acg")),
            "Antiagrégants plaquettaires": _t2.checkbox("Antiagrégants",   key=WK("pt_aap")),
            "Bêta-bloquants":              _t1.checkbox("Bêtabloquants",   key=WK("pt_beta")),
            "Corticoïdes au long cours":   _t2.checkbox("Corticoïdes",     key=WK("pt_cort")),
            "IMAO (inhibiteurs MAO)":      _t1.checkbox("IMAO",            key=WK("pt_imao")),
            "Chimiothérapie en cours":     _t2.checkbox("Chimio",          key=WK("pt_chimo")),
        }

        st.divider()
        _alg = st.text_input("🚫 Allergies connues", value=SS.get("alg", ""), key="pt_alg",
                              placeholder="ex: Pénicilline, AINS...")
        _o2  = st.checkbox("💨 O₂ supplémentaire à l'admission", key=WK("pt_o2"))
        _other = st.multiselect("Autres ATCD", [a for a in ATCD if a not in list(_atcd_checks.keys())],
                                key="pt_atcd_other")
        st.divider()
        H('<div class="card-title">⚖️ Fragilité — Clinical Frailty Scale (Rockwood 2005)</div>')
        _cfs_n = st.select_slider("CFS", options=list(range(1,10)), value=1,
            key=WK("pt_cfs"),
            format_func=lambda x: {1:"1–Très robuste",2:"2–En forme",3:"3–Bien portant",
                4:"4–Vulnérable",5:"5–Fragile léger",6:"6–Fragile modéré",
                7:"7–Fragile sévère",8:"8–Très fragile",9:"9–Fin de vie"}[x])
        if _cfs_n >= 7:
            AL(f"CFS {_cfs_n} — Fragilité sévère — Triage majoré automatiquement (worst-case)", "warning")
        elif _cfs_n >= 5:
            AL(f"CFS {_cfs_n} — Fragilité modérée — Adapter doses et surveillance", "info")

        # Consolidation SS
        _all = {**_atcd_checks, **_risk_checks, **_trt_checks}
        SS["atcd"]        = [lbl for lbl, chk in _all.items() if chk] + _other
        SS["atcd_checks"] = _atcd_checks
        SS["risk_checks"] = _risk_checks
        SS["trt_checks"]  = _trt_checks
        SS["alg"]         = _alg
        SS["o2"]          = _o2
        SS.det = {**(SS.det or {}), "cfs_score": _cfs_n}
        atcd = SS["atcd"]; alg = SS["alg"]; o2 = SS["o2"]
        atcd_checks = _atcd_checks; risk_checks = _risk_checks; trt_checks = _trt_checks

        # ── Alertes pharmacovigilance immédiates ───────────────────────────────
        st.divider()
        H('<div class="card-title">🚨 Alertes Pharmacovigilance</div>')
        _alerts_pv = []
        if _trt_checks.get("IMAO (inhibiteurs MAO)"):
            _alerts_pv.append(("IMAO — Tramadol CONTRE-INDIQUÉ ABSOLU", "danger"))
        if _atcd_checks.get("Insuffisance rénale chronique"):
            _alerts_pv.append(("Insuff. rénale — Tous les AINS contre-indiqués", "danger"))
        if _trt_checks.get("Anticoagulants/AOD"):
            _alerts_pv.append(("Anticoagulants — Tout trauma = Tri 2 minimum", "warning"))
        if _atcd_checks.get("Immunodépression") or _trt_checks.get("Chimiothérapie en cours"):
            _alerts_pv.append(("Immunodéprimé — Seuil fébrile 38.3 °C", "warning"))
        if _risk_checks.get("Grossesse"):
            _alerts_pv.append(("Grossesse — AINS déconseillés au T3", "warning"))
        if _trt_checks.get("Bêta-bloquants"):
            _alerts_pv.append(("Bêtabloquants — FC peut être masquée", "warning"))
        if _atcd_checks.get("Drépanocytose"):
            _alerts_pv.append(("Drépanocytose — Morphine précoce si EVA ≥ 6", "warning"))
        if _atcd_checks.get("Asthme"):
            _alerts_pv.append(("Asthme — AINS déconseillés (risque bronchospasme)", "warning"))
        if _alg:
            _alerts_pv.append((f"Allergies déclarées : {_alg}", "danger"))

        if _alerts_pv:
            for _msg, _lvl in _alerts_pv:
                AL(_msg, _lvl)
        else:
            st.success("✅ Aucune alerte pharmacovigilance")



    # ════════════════════════════════════════════════════════════════════════════
    # ONGLET 1 — TRIAGE (page unique, workflow linéaire de haut en bas)
    # ════════════════════════════════════════════════════════════════════════════
    with T[1]:
        try:
            render_triage()
        except Exception as _e:
            st.error(f"⚠️ Erreur onglet Triage — rechargez la page ({type(_e).__name__}: {_e})")

    # ════════════════════════════════════════════════════════════════════════════
    # ONGLET 2 — IA TRIAGE (modèle v2 : 13 features + enrichissement MIMIC-III)
    # ════════════════════════════════════════════════════════════════════════════
    with T[2]:
        H('<div style="background:linear-gradient(135deg,#7C3AED,#A855F7);color:#fff;'
          'border-radius:10px;padding:12px 16px;margin-bottom:12px;">'
          '<div style="font-size:.72rem;opacity:.75;text-transform:uppercase;letter-spacing:.1em;">'
          'Modèle v2 · KTAS + MIMIC-III</div>'
          '<div style="font-size:1rem;font-weight:700;">Triage par IA</div></div>')

        from ml.triage_predictor import get_ml_priority

        # Pré-remplissage centralisé depuis le contexte patient
        _payload = build_triage_payload(SS)
        _avpu_auto    = _payload["avpu"]
        _trauma_auto  = bool(_payload["injury"])

        AL("✓ Vitaux pré-remplis depuis l'onglet Triage. Ajustez si besoin.", "info")
        explain("ia_triage")
        explain("avpu", compact=True)

        with st.form("ia_triage_form_v2"):
            st.subheader("Saisie des constantes vitales")
            col1, col2 = st.columns(2)
            with col1:
                _fc   = st.number_input("Fréquence cardiaque (bpm)",     20, 250, int(_payload["fc"]),   step=1)
                _fr   = st.number_input("Fréquence respiratoire (/min)", 4,  60,  int(_payload["fr"]),   step=1)
                _pas  = st.number_input("PAS (mmHg)",                    40, 300, int(_payload["pas"]),  step=1)
                _pad  = st.number_input("PAD (mmHg)",                    20, 200, int(_payload["pad"]),  step=1)
            with col2:
                _spo2 = st.number_input("SpO2 (%)",                      50, 100, int(_payload["spo2"]), step=1)
                _temp = st.number_input("Température (°C)",              30.0, 45.0, float(_payload["temp"]), step=0.1, format="%.1f")
                _avpu_lbls = ["A — Alerte", "V — Réactif voix", "P — Réactif douleur", "U — Inconscient"]
                _avpu_idx  = {"A": 0, "V": 1, "P": 2, "U": 3}.get(_avpu_auto, 0)
                _avpu_lbl  = st.selectbox("AVPU (dérivé GCS)", _avpu_lbls, index=_avpu_idx,
                                          help="Mapping automatique depuis le GCS — modifiable")
                _nrs  = st.number_input("Douleur NRS (0-10)",            0,  10,  int(_payload["nrs_pain"]), step=1)

            col3, col4 = st.columns(2)
            with col3:
                _amb  = st.checkbox("Arrivée en ambulance", value=False)
            with col4:
                _inj  = st.checkbox("Traumatisme / lésion",  value=_trauma_auto,
                                     help="Auto-détecté depuis le motif")

            submitted = st.form_submit_button("🤖 Analyser le triage", type="primary", use_container_width=True)

        if submitted:
            _avpu = _avpu_lbl.split(" ", 1)[0]   # "A", "V", "P", "U"

            res = get_ml_priority({
                "fc":   _fc,   "fr":   _fr,   "pas":  _pas,  "pad":  _pad,
                "spo2": _spo2, "temp": _temp, "avpu": _avpu, "nrs_pain": _nrs,
                "arrival_ambulance": int(_amb),
                "injury":            int(_inj),
            })

            if res["erreur"]:
                AL(f"Erreur prédiction : {res['erreur']}", "danger")
            else:
                couleur = res["couleur"]
                st.markdown(
                    f'<div style="background:{couleur};color:white;padding:18px;'
                    f'border-radius:10px;text-align:center;font-weight:900;'
                    f'box-shadow:0 4px 12px rgba(0,0,0,.2);margin:8px 0;">'
                    f'<div style="font-size:24px;">{res["label"]}</div>'
                    f'<div style="font-size:14px;opacity:.85;margin-top:4px;">'
                    f'Confiance : {res["confiance"]:.0%}</div></div>',
                    unsafe_allow_html=True,
                )

                if res["alerte_p1"]:
                    AL("🚨 ALERTE P1 — Probabilité critique ≥ 25 % — Vérifier hémodynamique et appeler médecin", "danger")

                # Probabilités par priorité
                _proba_cols = st.columns(5)
                for _i, _p in enumerate(sorted(res["probabilites"].keys())):
                    _proba_cols[_i].metric(f"P{_p}", f"{res['probabilites'][_p]:.0%}")

                # Features dérivées (shock index, MAP, PP)
                _fi = res.get("features_input", {})
                _si  = _fi.get("shock_index", 0)
                _map = _fi.get("map_val", 0)
                _pp  = _fi.get("pp", 0)
                _si_color = "#EF4444" if _si > 1.0 else "#F59E0B" if _si > 0.8 else "#22C55E"
                st.markdown(
                    f'<div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;">'
                    f'<div style="background:#1E293B;padding:8px 12px;border-radius:8px;flex:1;">'
                    f'<span style="font-size:.7rem;color:#94A3B8;">Index de choc</span><br>'
                    f'<span style="font-size:1.2rem;font-weight:700;color:{_si_color};">{_si:.2f}</span></div>'
                    f'<div style="background:#1E293B;padding:8px 12px;border-radius:8px;flex:1;">'
                    f'<span style="font-size:.7rem;color:#94A3B8;">PAM</span><br>'
                    f'<span style="font-size:1.2rem;font-weight:700;color:#E2E8F0;">{_map:.0f} mmHg</span></div>'
                    f'<div style="background:#1E293B;padding:8px 12px;border-radius:8px;flex:1;">'
                    f'<span style="font-size:.7rem;color:#94A3B8;">Pression pulsée</span><br>'
                    f'<span style="font-size:1.2rem;font-weight:700;color:#E2E8F0;">{_pp:.0f} mmHg</span></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ════════════════════════════════════════════════════════════════════════════
    # ONGLET 3 — PHARMACIE (filtrée par motif, doses calculées)
    # ════════════════════════════════════════════════════════════════════════════
    with T[3]:
        try:
            render_pharmacie()
        except Exception as _e:
            st.error(f"⚠️ Erreur onglet Pharmacie — rechargez la page ({type(_e).__name__}: {_e})")

    # ════════════════════════════════════════════════════════════════════════════
    # ONGLET 4 — SCORES CLINIQUES
    # ════════════════════════════════════════════════════════════════════════════
    with T[4]:
        try:
            render_scores()
        except Exception as _e:
            st.error(f"⚠️ Erreur onglet Scores — rechargez la page ({type(_e).__name__}: {_e})")

    # ═══════════════════════════════════════════════════════════════════════════
    # ONGLET 5 — 🛠️ OUTILS CLINIQUES
    # ═══════════════════════════════════════════════════════════════════════════
    with T[5]:
        H('''<div style="background:linear-gradient(135deg,#1E3A5F,#1D4ED8);color:#fff;
            border-radius:12px;padding:14px 18px;margin-bottom:12px;">
          <div style="display:flex;align-items:center;gap:12px;">
            <div style="font-size:2rem;">🛠️</div>
            <div>
              <div style="font-size:.72rem;opacity:.75;text-transform:uppercase;letter-spacing:.12em;">Aide à la décision</div>
              <div style="font-size:1rem;font-weight:800;">Outils Cliniques Urgences</div>
              <div style="font-size:.72rem;opacity:.75;margin-top:2px;">RSI · Volémie · Broselow · Opioïdes · DFGe · Stroke · Défibrillateur</div>
            </div>
          </div>
        </div>''')

        _OT = st.tabs(["💉 RSI", "💧 Volémie", "👶 Broselow",
                        "🔄 Opioïdes", "🧪 Rein/Na", "🧠 Stroke",
                        "⚡ Défibrillateur", "🩸 Hémorragie digest."])

        # ── OT[0] RSI ────────────────────────────────────────────────────────
        with _OT[0]:
            H('<div class="card-title">💉 Séquence Rapide d\'Intubation (RSI)</div>')
            st.caption("SFAR 2017 / ERC 2021 — Doses calculées sur le poids réel")
            _r1, _r2 = st.columns(2)
            _rsi_hyp = _r1.selectbox("Hypnotique", list(RSI_AGENTS.keys()), key=WK("rsi_hyp"))
            _rsi_cur = _r2.selectbox("Curare",     list(CURARES_RSI.keys()), key=WK("rsi_cur"))
            _rsi_res = calculer_rsi(poids, age, _rsi_hyp, _rsi_cur)
            for nom, ag in _rsi_res["agents"].items():
                _bg = "#7F1D1D" if "Atropine" not in nom else "#1E3A5F"
                _ci_html = (
                    f'<div style="font-size:.72rem;color:#FCA5A5;margin-top:3px;">⚠️ CI : {" | ".join(ag["ci"])}</div>'
                    if ag["ci"] else ""
                )
                H(f'<div style="background:{_bg};color:#fff;border-radius:8px;padding:10px 14px;margin:5px 0;">'
                  f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                  f'<div style="font-weight:700;font-size:.85rem;">{nom}</div>'
                  f'<div style="font-family:monospace;font-size:1.4rem;font-weight:900;">{ag["dose_mg"]} mg</div>'
                  f'</div><div style="font-size:.72rem;opacity:.8;margin-top:3px;">{ag["voie"]} — {ag["note"][:60]}</div>'
                  f'{_ci_html}</div>')
            st.divider()
            H('<div class="card-title">📋 Ordre d\'exécution RSI</div>')
            for step in _rsi_res["ordre"]:
                st.markdown(f"- {step}")
            st.info(f"Sonde IT : **{_rsi_res['sonde_it']}** | Canule Guedel : **{_rsi_res['guedel']}**")
            st.caption(_rsi_res["source"])

        # ── OT[1] VOLÉMIE ────────────────────────────────────────────────────
        with _OT[1]:
            H('<div class="card-title">💧 Recharge Volémique</div>')
            st.caption("SSC 2021 / ATLS 11th / ESPGHAN 2014")
            _vi = st.selectbox("Indication",
                ["sepsis","trauma","deshy","general"],
                format_func=lambda x: {"sepsis":"Sepsis","trauma":"Trauma hémorragique","deshy":"Déshydratation","general":"Général"}[x],
                key=WK("vol_ind"))
            _rv = calculer_recharge_volemique(poids, age, _vi)
            H(f'<div style="background:{_rv["couleur"]}20;border:2px solid {_rv["couleur"]};border-radius:10px;padding:14px;margin:8px 0;text-align:center;">'
              f'<div style="font-size:.72rem;color:#64748B;">{_rv["titre"]}</div>'
              f'<div style="font-size:1.8rem;font-weight:900;color:{_rv["couleur"]};">{_rv["bolus_ml"]} ml</div>'
              f'<div style="font-size:.78rem;color:#94A3B8;">{_rv["soluté"]} en {_rv["débit"]}</div></div>')
            for b_info in _rv["bolus_list"]:
                ok_col = "#22C55E" if b_info["num"] == 1 else "#F59E0B" if b_info["num"] == 2 else "#EF4444"
                H(f'<div style="display:flex;justify-content:space-between;background:#0F172A;border-radius:6px;padding:8px 12px;margin:3px 0;">'
                  f'<span style="color:#94A3B8;font-size:.75rem;">Bolus {b_info["num"]}</span>'
                  f'<span style="color:{ok_col};font-weight:700;font-family:monospace;">{b_info["ml"]} ml</span>'
                  f'<span style="color:#64748B;font-size:.72rem;">Cumulé : {b_info["total_ml"]} ml ({b_info["total_ml_kg"]} ml/kg)</span></div>')
            AL(_rv["info"], "info")
            AL(_rv["note_max"], "warning")
            st.caption(_rv["source"])

        # ── OT[2] BROSELOW ──────────────────────────────────────────────────
        with _OT[2]:
            H('<div class="card-title">👶 Broselow — Doses pédiatriques par taille</div>')
            st.caption("Broselow JB et al., Ann Emerg Med 1988 / mise à jour 2018")
            _taille_br = st.number_input("Taille enfant (cm)", 40, 160, min(max(int(SS.taille or 100), 40), 160), 1, key=WK("br_t"))
            _br = broselow(float(_taille_br))
            _br_col = _br["hex_couleur"]
            H(f'<div style="background:{_br_col};border-radius:12px;padding:16px;text-align:center;margin:10px 0;">'
              f'<div style="font-size:1.4rem;font-weight:900;color:#0F172A;">{_br["couleur"].upper()}</div>'
              f'<div style="font-size:.8rem;color:#1E293B;">Poids estimé : {_br["poids_estimé"]} kg</div></div>')
            if _br.get("doses"):
                for nom_dose, val_dose in _br["doses"].items():
                    H(f'<div style="display:flex;justify-content:space-between;border-bottom:1px solid #1E293B;padding:6px 0;font-size:.78rem;">'
                      f'<span style="color:#94A3B8;">{nom_dose}</span>'
                      f'<span style="color:#E2E8F0;font-weight:700;font-family:monospace;">{val_dose}</span></div>')
            st.caption(_br.get("source","Broselow 2018"))

        # ── OT[3] OPIOÏDES ──────────────────────────────────────────────────
        with _OT[3]:
            H('<div class="card-title">🔄 Convertisseur Opioïdes — Équianalgésie</div>')
            st.caption("BCFI 2024 / OMS 2019 / BNF 2024")
            AL("Toujours commencer à 50% de la dose calculée — titration obligatoire", "warning")
            _o1, _o2 = st.columns(2)
            _op_src = _o1.selectbox("Molécule actuelle", list(OPIOIDES_RATIO_IV.keys()), key=WK("op_src"))
            _op_dst = _o2.selectbox("Convertir en",      list(OPIOIDES_RATIO_IV.keys()),
                                     index=min(3, len(OPIOIDES_RATIO_IV)-1), key=WK("op_dst"))
            _op_dose = st.number_input(f"Dose de {_op_src} (mg)", 0.01, 1000.0, 10.0, 0.5, key=WK("op_d"))
            if _op_src != _op_dst:
                _oc = convertir_opioides(_op_src, _op_dose, _op_dst)
                if "erreur" not in _oc:
                    H(f'<div style="background:#0F172A;border-radius:10px;padding:16px;margin:10px 0;">'
                      f'<div style="color:#94A3B8;font-size:.72rem;">Équivalent morphine IV</div>'
                      f'<div style="color:#38BDF8;font-family:monospace;font-size:1.1rem;font-weight:700;">{_oc["morphine_iv_eq_mg"]} mg morphine IV</div>'
                      f'<div style="color:#94A3B8;font-size:.72rem;margin-top:8px;">Dose {_op_dst} calculée</div>'
                      f'<div style="color:#F59E0B;font-family:monospace;font-size:1.5rem;font-weight:900;">{_oc["dose_calculee_mg"]} mg</div>'
                      f'<div style="color:#22C55E;font-family:monospace;font-size:.9rem;margin-top:4px;">Démarrer à : {_oc["dose_demarrage_mg"]} mg (50%)</div></div>')
                    AL(_oc["avertissement"], "danger")
                    st.caption(_oc["source"])

        # ── OT[4] REIN / Na ──────────────────────────────────────────────────
        with _OT[4]:
            _rt1, _rt2 = st.tabs(["🔬 DFGe CKD-EPI", "🧂 Correction Na"])
            with _rt1:
                H('<div class="card-title">🔬 DFGe — CKD-EPI 2021</div>')
                st.caption("Inker LA et al., NEJM 2021 / KDIGO 2022 (sans coefficient racial)")
                _dk1, _dk2 = st.columns(2)
                _cr_umol = _dk1.number_input("Créatinine (µmol/L)", 30, 2000, 80, 5, key=WK("ck_cr"))
                _cr_sexe = _dk2.radio("Sexe", ["H","F"], key=WK("ck_sx"), horizontal=True)
                _dfge_r  = calculer_dfge(float(_cr_umol), age, _cr_sexe)
                _dfge_v  = _dfge_r["dfge"]
                _dfge_c  = _dfge_r["couleur"]
                H(f'<div style="background:{_dfge_c}20;border:2px solid {_dfge_c};border-radius:10px;padding:14px;text-align:center;margin:8px 0;">'
                  f'<div style="font-size:2.5rem;font-weight:900;color:{_dfge_c};font-family:monospace;">{_dfge_v}</div>'
                  f'<div style="font-size:.72rem;color:#94A3B8;">ml/min/1,73 m²</div>'
                  f'<div style="font-size:.8rem;font-weight:700;color:{_dfge_c};margin-top:4px;">{_dfge_r["stade"]}</div></div>')
                AL(_dfge_r["note"], "warning" if _dfge_v < 60 else "info")
                if _dfge_r["adaptations"]:
                    st.divider()
                    H('<div class="card-title">Adaptations posologiques requises</div>')
                    for adapt in _dfge_r["adaptations"]:
                        AL(adapt, "danger" if "🔴" in adapt else "warning")
                st.caption(_dfge_r["source"])
            with _rt2:
                H('<div class="card-title">🧂 Correction natrémie (hyperglycémie)</div>')
                st.caption("Hillier TA et al., NEJM 1999 / Katz MA, NEJM 1973")
                _na1, _na2 = st.columns(2)
                _na_mes  = _na1.number_input("Natrémie mesurée (mmol/L)", 110, 165, 135, 1, key=WK("na_m"))
                _gly_mml = _na2.number_input("Glycémie (mmol/L)", 1.0, 60.0, 5.5, 0.5, key=WK("na_g"))
                _na_res  = corriger_natrémie(float(_na_mes), float(_gly_mml))
                H(f'<div style="background:#0F172A;border-radius:10px;padding:14px;margin:10px 0;">'
                  f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
                  f'<span style="color:#94A3B8;font-size:.72rem;">Formule Katz</span>'
                  f'<span style="color:#38BDF8;font-family:monospace;font-weight:700;">{_na_res["na_corrige_katz"]} mmol/L</span></div>'
                  f'<div style="display:flex;justify-content:space-between;">'
                  f'<span style="color:#94A3B8;font-size:.72rem;">Formule Hillier (recommandée)</span>'
                  f'<span style="color:#22C55E;font-family:monospace;font-weight:900;font-size:1.1rem;">{_na_res["na_corrige_hillier"]} mmol/L</span></div></div>')
                AL(_na_res["interpretation"], _na_res["niveau"])
                st.caption(_na_res["source"])

        # ── OT[5] CODE STROKE ────────────────────────────────────────────────
        with _OT[5]:
            H('<div class="card-title">🧠 Code Stroke — Délais ESO 2021</div>')
            st.caption("ESO 2021 — Door-to-CT ≤ 25 min | Door-to-needle ≤ 60 min | Fenêtre ≤ 4,5h")
            _cs1, _cs2, _cs3 = st.columns(3)
            _cs_deb = _cs1.text_input("Heure début symptômes (HH:MM)", placeholder="08:30", key=WK("cs_d"))
            _cs_arr = _cs2.text_input("Heure arrivée urgences (HH:MM)", placeholder="09:00", key=WK("cs_a"))
            _cs_ct  = _cs3.text_input("Heure TDM cérébral (HH:MM)", placeholder="09:20", key=WK("cs_ct"))
            _cs = code_stroke_delais(_cs_deb or None, _cs_arr or None, _cs_ct or None)
            if "duree_symptomes_min" in _cs:
                _dure = _cs["duree_symptomes_min"]
                _fen  = _cs.get("fenetre_thrombolyse", False)
                _rest = _cs.get("temps_restant_thrombo_min", 0)
                _col_f = "#22C55E" if _fen else "#EF4444"
                H(f'<div style="background:{_col_f}20;border:2px solid {_col_f};border-radius:10px;padding:14px;text-align:center;margin:8px 0;">'
                  f'<div style="font-size:.72rem;color:#94A3B8;">Durée symptômes</div>'
                  f'<div style="font-size:2rem;font-weight:900;color:{_col_f};font-family:monospace;">{_dure} min</div>'
                  f'<div style="font-size:.8rem;color:{_col_f};font-weight:700;">{"✅ Fenêtre thrombolyse ouverte — " + str(_rest) + " min restantes" if _fen else "🔴 Fenêtre thrombolyse FERMÉE (> 4,5h)"}</div></div>')
            if "door_to_ct_min" in _cs:
                _dtct_col = "#22C55E" if _cs.get("door_to_ct_ok") else "#EF4444"
                AL(f"Door-to-CT : {_cs['door_to_ct_min']} min (objectif ≤ 25 min {'✅' if _cs.get('door_to_ct_ok') else '❌'})", "success" if _cs.get("door_to_ct_ok") else "danger")
            st.divider()
            H('<div class="card-title">Checklist Code Stroke</div>')
            for item in _cs["checklist"]:
                st.checkbox(item, key=WK(f"cs_{item[:15]}"))
            with st.expander("⚠️ Contre-indications thrombolyse"):
                for ci_item in _cs["ci_thrombolyse"]:
                    st.markdown(f"• {ci_item}")
            st.caption(_cs["source"])

        # ── OT[6] DÉFIBRILLATEUR ─────────────────────────────────────────────
        with _OT[6]:
            H('<div class="card-title">⚡ Défibrillateur — Énergie recommandée</div>')
            st.caption("ERC 2021 — Soar J et al. / ESC 2020 FA")
            _dj1, _dj2 = st.columns(2)
            _def_type = _dj1.selectbox("Type de choc",
                ["FV","TV sans pouls","FA","Flutter","TV tolérée"],
                key=WK("def_t"))
            _j = joules_defibrillateur(poids, age, _def_type)
            if "erreur" not in _j:
                _joules_rows = ""
                for label, key in [("1er choc","choc_1"),("2e choc / suivants","choc_2")]:
                    if key in _j:
                        _joules_rows += (
                            '<div style="display:flex;justify-content:space-between;padding:6px 0;'
                            'border-bottom:1px solid #1E293B;">'
                            f'<span style="color:#64748B;font-size:.72rem;">{label}</span>'
                            f'<span style="color:#F59E0B;font-family:monospace;font-weight:900;font-size:1.1rem;">{_j[key]}</span></div>'
                        )
                H(
                    '<div style="background:#0F172A;border-radius:10px;padding:16px;margin:8px 0;">'
                    f'<div style="color:#94A3B8;font-size:.72rem;margin-bottom:8px;">{_j["type"]}</div>'
                    f'{_joules_rows}</div>'
                )
                if "note" in _j:
                    AL(_j["note"], "info")
            st.caption(_j.get("source","ERC 2021"))

        # ── OT[7] HÉMORRAGIE DIGESTIVE ───────────────────────────────────────
        with _OT[7]:
            H('<div class="card-title">🩸 Glasgow-Blatchford — Hémorragie digestive haute</div>')
            st.caption("Blatchford O et al., Lancet 2000 — Score 0 = ambulatoire possible")
            _hd1, _hd2 = st.columns(2)
            _hd_ure  = _hd1.number_input("Urée sanguine (mmol/L)", 0.0, 60.0, 5.0, 0.5, key=WK("hd_u"))
            _hd_hb   = _hd2.number_input("Hémoglobine (g/dL)", 4.0, 20.0, 13.0, 0.5, key=WK("hd_h"))
            _hd_sx   = _hd1.radio("Sexe", ["H","F"], key=WK("hd_sx"), horizontal=True)
            _hd_tach = _hd2.checkbox("Tachycardie ≥ 100 bpm", value=(SS.v_fc or 80) >= 100, key=WK("hd_tc"))
            _hd_mel  = _hd1.checkbox("Méléna présent", key=WK("hd_ml"))
            _hd_syn  = _hd2.checkbox("Syncope à l'entrée", key=WK("hd_sy"))
            _hd_hep  = _hd1.checkbox("Hépatopathie chronique", key=WK("hd_hp"))
            _hd_ic   = _hd2.checkbox("Insuffisance cardiaque", key=WK("hd_ic"))
            _hd_pas  = st.number_input("PAS (mmHg)", 50, 220, int(SS.v_pas or 120), key=WK("hd_p"))
            _gb = calculer_blatchford(float(_hd_ure), float(_hd_hb), float(_hd_pas),
                                       _hd_sx, _hd_tach, _hd_mel, _hd_syn, _hd_hep, _hd_ic)
            _gb_v = _gb["score_val"]
            _gb_c = "#EF4444" if _gb_v >= 6 else "#F59E0B" if _gb_v >= 1 else "#22C55E"
            H(f'<div style="background:{_gb_c}20;border:2px solid {_gb_c};border-radius:10px;padding:14px;text-align:center;margin:10px 0;">'
              f'<div style="font-size:2.5rem;font-weight:900;color:{_gb_c};font-family:monospace;">{_gb_v}/23</div>'
              f'<div style="font-size:.8rem;color:{_gb_c};font-weight:700;">{_gb["interpretation"]}</div></div>')
            AL(_gb["recommendation"], _gb["niveau"])
            st.caption(_gb["source"])

    with T[6]:
        _ST = st.tabs(["🔄 Réévaluation", "📜 Historique", "📡 SBAR"])

        with _ST[0]:
            H('<div id="akir-anchor-reev" style="scroll-margin-top:80px;"></div>')
            if not SS.uid_cur:
                AL("Enregistrer d'abord un patient dans l'onglet ⚡ Triage", "info")
            else:
                st.caption(f"Patient actif : {SS.uid_cur}")
                _rc1, _rc2, _rc3 = st.columns(3)
                _re_temp = _rc1.number_input("T°",  30.0, 45.0, float(SS.v_temp), 0.1, key="re_t")
                _re_fc   = _rc1.number_input("FC",   20, 220, int(SS.v_fc),   key="re_fc")
                _re_pas  = _rc2.number_input("PAS",  40, 260, int(SS.v_pas),  key="re_pas")
                _re_spo2 = _rc2.number_input("SpO2", 50, 100, int(SS.v_spo2), key="re_sp")
                _re_fr   = _rc3.number_input("FR",    5,  60, int(SS.v_fr),   key="re_fr")
                _re_gcs  = _rc3.number_input("GCS",   3,  15, int(SS.v_gcs),  key="re_gcs")
                try:
                    _ren2, _ = calculer_news2(_re_fr, _re_spo2, o2, _re_temp, _re_pas,
                                              _re_fc, _re_gcs, SS.v_bpco)
                except ValueError as _exc:
                    st.error(f"🚨 NEWS2 réévaluation indisponible — {_exc}")
                    _ren2 = None

                if _ren2 is not None:
                    _reniv, _rejust, _ = french_triage(SS.motif, SS.det, _re_fc, _re_pas, _re_spo2,
                                                        _re_fr, _re_gcs, _re_temp, age, _ren2, SS.gl)
                    _baseline = SS.v_news2 if SS.v_news2 is not None else _ren2
                    _delta = _ren2 - _baseline
                    st.metric("NEWS2 réévaluation", _ren2, delta=_delta, delta_color="inverse")
                    TRI_CARD_INLINE(_reniv, _rejust, _ren2)
                    if _delta >= 3:
                        AL(f"🔴 Δ NEWS2 +{_delta} — Aggravation rapide — Appel médical IMMÉDIAT", "danger")
                    elif _delta > 0:
                        AL(f"NEWS2 +{_delta} — Score en hausse — Surveillance renforcée", "warning")
                    elif _delta <= -2:
                        AL(f"Δ NEWS2 {_delta} — Amélioration clinique confirmée", "success")
                    elif _delta < 0:
                        AL(f"NEWS2 {_delta} — Score en légère baisse", "success")
                    SS.det = {**(SS.det or {}), "n2_precedent": SS.v_news2}

                # Alertes temporelles
                if SS.t_reev:
                    _mins = (datetime.now() - SS.t_reev).total_seconds() / 60
                    _del_cible = {"M":5,"1":5,"2":15,"3A":30,"3B":60}.get(SS.niv, 60)
                    if 25 <= _mins <= 35:
                        AL("⏱ 30 min — Réévaluation douleur POST-ANTALGIE obligatoire (Circulaire 2014)", "warning")
                    elif 55 <= _mins <= 65:
                        AL("⏱ 60 min — Réévaluation POST-ANTALGIE obligatoire", "warning")
                    if _mins > _del_cible:
                        AL(f"⏱ Délai cible Tri {SS.niv} ({_del_cible} min) DÉPASSÉ — Relancer le médecin", "danger")

                if st.button("✅ Enregistrer la réévaluation", key="re_save", use_container_width=True):
                    SS.reevs.append({
                        "h": datetime.now().strftime("%H:%M"),
                        "fc": _re_fc, "pas": _re_pas, "spo2": _re_spo2,
                        "fr": _re_fr, "gcs": _re_gcs, "temp": _re_temp,
                        "n2": _ren2, "niv": _reniv,
                    })
                    st.success(f"Réévaluation à {SS.reevs[-1]['h']} — Tri {_reniv}")

            if SS.reevs:
                COURBE_VITAUX(SS.reevs)

            # Règle des 5B
            st.divider()
            H('<div class="card-title">🔒 Sécurité injection — Règle des 5B (AR 78 AFMPS 2019)</div>')
            _med_5b = st.selectbox("Médicament", [
                "Paracétamol IV", "Dipidolor® IV", "Morphine IV", "Adrénaline IM",
                "Ceftriaxone IV", "Glucose 30% IV", "Litican® (Alizapride) IV/IM", "Tramadol",
                "Midazolam buccal", "Acide tranexamique IV", "Autre",
            ], key="re_5b_med")
            _dose_5b = st.text_input("Dose", key="re_5b_dose", placeholder="ex: 1 g IV en 15 min")
            _voie_5b = st.selectbox("Voie", ["IV","IM","SC","Buccale","IN","Nébulisation","PO"], key="re_5b_voie")
            CHECKLIST_5B(medicament=_med_5b, dose=_dose_5b, voie=_voie_5b,
                         poids=poids, uid=SS.uid_cur or SS.uid)

        with _ST[1]:
            _reg = charger_registre()
            if _reg:
                CARD("Session — Statistiques", "")
                _rs1, _rs2, _rs3 = st.columns(3)
                _rs1.metric("Patients", len(_reg))
                _rs2.metric("Critiques", sum(1 for r in _reg if r.get("niv") in ("M","1","2")))
                _rs3.metric("NEWS2 moyen", round(sum(r.get("n2",0) for r in _reg)/max(1,len(_reg)),1))
                CARD_END()

            CARD("Registre RGPD anonyme", "")
            if not _reg:
                st.info("Aucun patient dans cette session")
            else:
                for _r in _reg[:20]:
                    _rc = st.columns([1,3,1,1])
                    _rc[0].caption((_r.get("heure","") or "")[-5:])
                    _rc[1].write(_r.get("motif",""))
                    _rc[2].write(f"**Tri {_r.get('niv','')}**")
                    _rc[3].caption(_r.get("uid",""))
            CARD_END()

            if _reg:
                _out = io.StringIO()
                _w = csv_mod.writer(_out)
                _w.writerow(["uid","heure","motif","niv","n2","fc","pas","spo2","fr","temp","gcs","op"])
                for _r in _reg:
                    _w.writerow([_r.get(k,"") for k in ["uid","heure","motif","niv","n2","fc","pas","spo2","fr","temp","gcs","op"]])
                st.download_button("📥 Export CSV", data=_out.getvalue(),
                    file_name=f"akir_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv", use_container_width=True)
            if st.button("🔐 Intégrité audit", key="audit_int", use_container_width=True):
                _au = audit_verifier_integrite()
                AL(_au.get("message",""), "success" if _au.get("ok") else "danger")

        with _ST[2]:
            H('<div id="akir-anchor-sbar" style="scroll-margin-top:80px;"></div>')
            explain("sbar", compact=True)
            if not SS.niv:
                AL("Calculer d'abord le triage (onglet ⚡ Triage)", "info")
            else:
                _sbar = build_sbar(age, SS.motif, SS.cat, atcd, alg, o2,
                    SS.v_temp, SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr, SS.v_gcs,
                    SS.eva, SS.v_news2, SS.niv, SS.just, SS.crit,
                    SS.op or "IAO", SS.gl)
                SBAR_RENDER(_sbar, key_suffix="_suivi")

    with T[7]:
        render_readmission()

    with T[8]:
        render_mortality()

    with T[9]:
        _intro_sub, _glossary_sub = st.tabs(["📖 Présentation", "❓ Glossaire pédagogique"])
        with _intro_sub:
            _render_presentation()
        with _glossary_sub:
            glossary_grid()

    # ── Footer légal — affiché une seule fois ──────────────────────────────
    st.divider()
    st.warning("🤖 **Avertissement IA** : Le modèle de triage par IA est expérimental et ne remplace pas le jugement clinique de l'infirmier IAO. Utilisez-le uniquement comme aide complémentaire.")
    DISC()

    # ══ BOTTOM NAV MOBILE — 4 actions principales toujours 1 tap ═════════════
    # data-tabs    = séquence de fragments de texte d'onglets à cliquer (séparés par "|")
    # data-anchor  = ID HTML cible à scroller après navigation
    H("""
    <nav class="bottom-nav" role="navigation" aria-label="Navigation rapide IAO">
      <button class="bnav-btn" data-tabs="Triage" data-anchor="akir-anchor-vitaux"
              aria-label="Aller aux constantes vitales">
        <span class="bnav-ico">📊</span><span class="bnav-lbl">Vitaux</span>
      </button>
      <button class="bnav-btn" data-tabs="Triage" data-anchor="akir-anchor-triage"
              aria-label="Aller à la validation triage">
        <span class="bnav-ico">⚡</span><span class="bnav-lbl">Triage</span>
      </button>
      <button class="bnav-btn" data-tabs="Suivi|SBAR" data-anchor="akir-anchor-sbar"
              aria-label="Générer SBAR pour transmission DPI">
        <span class="bnav-ico">📡</span><span class="bnav-lbl">SBAR</span>
      </button>
      <button class="bnav-btn" data-tabs="Suivi|Réévaluation" data-anchor="akir-anchor-reev"
              aria-label="Réévaluation rapide">
        <span class="bnav-ico">🔄</span><span class="bnav-lbl">Réév.</span>
      </button>
    </nav>
    """)

    # Script de navigation — match d'onglet par texte (robuste aux ré-ordonnancements)
    # + scroll smooth vers l'ancre. Pattern d'attache périodique pour survivre aux re-runs.
    H("""
    <script>
    (function() {
      const doc = window.parent ? window.parent.document : document;

      function findTabByText(fragment) {
        const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
        const norm = fragment.toLowerCase();
        for (const t of tabs) {
          const txt = (t.textContent || '').toLowerCase();
          if (txt.includes(norm)) return t;
        }
        return null;
      }

      function akirNavigate(tabsSequence, anchorId) {
        const fragments = (tabsSequence || '').split('|').filter(Boolean);
        let delay = 0;
        for (const frag of fragments) {
          setTimeout(function() {
            const tab = findTabByText(frag);
            if (tab) tab.click();
          }, delay);
          delay += 140;
        }
        // Scroll vers l'ancre après que tous les tabs aient été cliqués
        setTimeout(function() {
          const el = doc.getElementById(anchorId);
          if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'});
        }, delay + 120);
      }

      function attachHandlers() {
        // Toute "balise navigation" reconnue : bouton bottom nav + CTA next-action
        const btns = doc.querySelectorAll('[data-tabs][data-anchor]');
        btns.forEach(function(btn) {
          if (btn.dataset.akirBound === '1') return;
          btn.dataset.akirBound = '1';
          btn.addEventListener('click', function(e) {
            e.preventDefault();
            const t = btn.dataset.tabs;
            const a = btn.dataset.anchor;
            akirNavigate(t, a);
            doc.querySelectorAll('.bnav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            setTimeout(() => btn.classList.remove('active'), 1200);
          }, {passive: false});
        });
      }

      attachHandlers();
      // Ré-attache périodiquement pour survivre aux re-runs Streamlit
      setInterval(attachHandlers, 1500);
    })();
    </script>
    """)

except Exception as _e:
    st.error(f"🚨 Erreur : {_e}")
    st.code(traceback.format_exc(), language="text")
