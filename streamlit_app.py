# streamlit_app.py — AKIR-IAO v19.0 — Système Expert Grade Hospitalier
# Développeur : Ismail Ibn-Daifa — Hainaut, Wallonie, Belgique
# UX refonte : "One-screen workflow" — confort IAO urgences — Mobile-first

import streamlit as st
import uuid, io, csv as csv_mod, traceback
from datetime import datetime

st.set_page_config(
    page_title="AKIR-IAO v19.0",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from config import *
from clinical.news2 import calculer_news2, n2_meta
from clinical.triage import french_triage, verifier_coherence
from clinical.scores import (
    calculer_gcs, calculer_qsofa, calculer_heart,
    calculer_timi, evaluer_fast, calculer_algoplus, evaluer_cfs,
    calculer_wells_tvp, calculer_wells_ep, calculer_nihss,
    calculer_sofa_partiel, calculer_curb65,
    regle_ottawa_cheville, regle_canadian_ct,
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
from persistence.registry import enregistrer_patient, charger_registre
from persistence.audit import audit_verifier_integrite
from ui.styles import load_css
from ui.components import (
    H, SEC, AL, CARD, CARD_END, PURPURA, N2_BANNER,
    GAUGE, VITAUX, TRI_CARD_INLINE, TRI_BANNER_FIXED,
    RX, RX_LOCK, GLYC_WIDGET, BPCO_WIDGET, SI_WIDGET,
    SBAR_RENDER, DISC, build_sbar, EVA_BAR,
)

MOTS_CAT       = FRENCH_MOTS_CAT
MOTIFS_RAPIDES = FRENCH_MOTIFS_RAPIDES

# ── Session State ─────────────────────────────────────────────────────────────
SS = st.session_state
_defaults = {
    "op": "", "sid": str(uuid.uuid4())[:8].upper(), "uid": None,
    "t_arr": None, "t_cont": None, "t_reev": None,
    "v_temp": 37.0, "v_fc": 80, "v_pas": 120,
    "v_spo2": 98, "v_fr": 16, "v_gcs": 15,
    "v_news2": 0, "v_bpco": False,
    "age": 45, "age_mois": 3, "poids": 70, "taille": 170,
    "alg": "", "o2": False, "atcd_other": [],
    "motif": "", "cat": "", "eva": 0, "gl": None,
    "niv": None, "just": "", "crit": "",
    "det": {}, "uid_cur": None,
    "histo": [], "reevs": [],
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

def _n2() -> int:
    n2, _ = calculer_news2(
        SS.v_fr, SS.v_spo2, SS.o2,
        SS.v_temp, SS.v_pas, SS.v_fc, SS.v_gcs, SS.v_bpco)
    SS.v_news2 = n2
    return n2

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

# ── CSS additionnel inline UX ─────────────────────────────────────────────────
st.markdown("""<style>
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
  .block-container { padding: .4rem .5rem 4rem !important; }
  button, .stButton > button { min-height: 48px !important; font-weight: 700 !important; }
}
</style>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Minimaliste (PC) : chrono + reset
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    SEC("AKIR-IAO v19.0")
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
        _el = (datetime.now() - SS.t_arr).total_seconds()
        _m, _s = divmod(int(_el), 60)
        _col = "#EF4444" if _el > 600 else ("#F59E0B" if _el > 300 else "#22C55E")
        H(f'<div style="text-align:center;font-family:monospace;font-size:2rem;font-weight:700;color:{_col};">{_m:02d}:{_s:02d}</div>')
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
      <span class="sticky-badge badge-triage {_niv_css}" style="font-size:.7rem;">{_niv_txt}</span>
      {"<span class='sticky-badge' style='color:#EF4444;border-color:#FCA5A5;background:#FEF2F2;'>N2={SS.v_news2}</span>" if SS.v_news2 >= 5 else ""}
      {"<span class='badge-chrono'>" + _timer_txt + "</span>" if _timer_txt else ""}
    </div>""")


try:
    # ══ EN-TÊTE COMPACT ══════════════════════════════════════════════════════
    H("""<div class="app-hdr" style="padding:10px 16px;margin-bottom:8px;">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;">
        <div>
          <div class="app-hdr-title" style="font-size:.95rem;">AKIR-IAO v19.0</div>
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

    # ══ ONGLETS PRINCIPAUX ════════════════════════════════════════════════════
    T = st.tabs([
        "👤 Patient",
        "⚡ Triage",
        "💊 Pharmacie",
        "🧬 Scores",
        "📋 Suivi",
    ])


    # ═══════════════════════════════════════════════════════════════════════════
    # ONGLET 0 — PROFIL PATIENT
    # ═══════════════════════════════════════════════════════════════════════════
    with T[0]:
        H('<div style="background:linear-gradient(135deg,#004A99,#0069D9);color:#fff;border-radius:10px;padding:12px 16px;margin-bottom:12px;">'
          '<div style="font-size:.65rem;opacity:.75;text-transform:uppercase;letter-spacing:.1em;">Renseigner en premier</div>'
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

        if _age_raw == 0:
            _am = st.number_input("Âge en mois", 0, 11, int(SS.get("age_mois") or 3), key="pt_am")
            SS["age_mois"] = _am; SS["age"] = round(_am / 12.0, 4)
            AL(f"Nourrisson {_am} mois — Seuils pédiatriques actifs", "info")
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

        # Consolidation SS
        _all = {**_atcd_checks, **_risk_checks, **_trt_checks}
        SS["atcd"]        = [lbl for lbl, chk in _all.items() if chk] + _other
        SS["atcd_checks"] = _atcd_checks
        SS["risk_checks"] = _risk_checks
        SS["trt_checks"]  = _trt_checks
        SS["alg"]         = _alg
        SS["o2"]          = _o2
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

        DISC()


    # ═══════════════════════════════════════════════════════════════════════════
    # ONGLET 1 — TRIAGE (page unique, workflow linéaire de haut en bas)
    # ═══════════════════════════════════════════════════════════════════════════
    with T[1]:

        # ── BLOC A : Chronomètre tactile ───────────────────────────────────────
        _ta1, _ta2 = st.columns(2)
        if _ta1.button("⏱ Marquer arrivée", key="tr_arr", use_container_width=True):
            SS.t_arr = datetime.now(); SS.histo = []; SS.reevs = []
            st.rerun()
        if _ta2.button("👨‍⚕️ 1er contact médecin", key="tr_cont", use_container_width=True):
            SS.t_cont = datetime.now(); st.rerun()

        if SS.t_arr:
            _el = (datetime.now() - SS.t_arr).total_seconds()
            _m, _s = divmod(int(_el), 60)
            _col = "#EF4444" if _el > 600 else ("#F59E0B" if _el > 300 else "#22C55E")
            _crit_txt = "<div style='font-size:.75rem;color:#fff;font-weight:700;'>⚠️ DÉLAI CRITIQUE</div>" if _el > 600 else ""
            H(f'<div class="timer-widget" style="background:{_col}20;border:2px solid {_col};">'
              f'<div><div class="timer-label">Temps depuis arrivée</div>'
              f'<div class="timer-digits" style="color:{_col};">{_m:02d}:{_s:02d}</div></div>'
              f'{_crit_txt}'
              f'</div>')

        st.divider()

        # ── BLOC B : Constantes vitales — saisie dense ─────────────────────────
        H('<div class="card-title">📊 Constantes vitales</div>')

        _vc1, _vc2, _vc3 = st.columns(3)
        SS.v_fc   = _vc1.number_input("FC (bpm)",   20, 220, int(SS.v_fc),         key="tr_fc",   label_visibility="visible")
        SS.v_pas  = _vc2.number_input("PAS (mmHg)", 40, 260, int(SS.v_pas),        key="tr_pas")
        SS.v_spo2 = _vc3.number_input("SpO2 (%)",   50, 100, int(SS.v_spo2),       key="tr_sp")
        _vc4, _vc5, _vc6 = st.columns(3)
        SS.v_fr   = _vc4.number_input("FR (/min)",   5,  60, int(SS.v_fr),         key="tr_fr")
        SS.v_temp = _vc5.number_input("T° (°C)",    30.0, 45.0, float(SS.v_temp), 0.1, key="tr_t")
        SS.v_gcs  = _vc6.number_input("GCS (3-15)",  3,  15, int(SS.v_gcs),        key="tr_gcs")

        SS.v_bpco = st.checkbox("BPCO — utiliser SpO2 cible 88-92 %", key=WK("tr_bp"),
                                 value=bool(SS.v_bpco or "BPCO" in atcd))
        if SS.v_bpco:
            AL("BPCO actif — SpO2 > 96 % sous O₂ = RISQUE hypercapnie", "warning")

        # NEWS2 calculé en temps réel
        _n2 = _n2()

        # Affichage NEWS2 inline avec code couleur
        _n2_color = "#7C3AED" if _n2 >= 9 else "#EF4444" if _n2 >= 7 else "#F59E0B" if _n2 >= 5 else "#22C55E" if _n2 >= 1 else "#3B82F6"
        _n2_risk  = ("CRITIQUE — Déchocage" if _n2 >= 9 else
                     "ÉLEVÉ — Appel médecin immédiat" if _n2 >= 7 else
                     "MODÉRÉ — Surveillance rapprochée" if _n2 >= 5 else
                     "Faible — Surveillance standard" if _n2 >= 1 else "Stable")
        _bpco_sub = ('<div style="font-size:.65rem;color:#64748B;">Echelle SpO2-2 (BPCO)</div>' if SS.v_bpco else '')
        H(f'<div class="news2-inline">'
          f'<div class="news2-number" style="color:{_n2_color};">{_n2}</div>'
          f'<div><div class="news2-label">NEWS2 / 20</div>'
          f'{_bpco_sub}'
          f'</div></div>')

        if _n2 >= 9:
            H('<div style="background:#4C1D95;color:#E879F9;border-radius:8px;padding:10px;text-align:center;font-weight:800;font-size:.9rem;animation:pulse 1.5s infinite;margin:6px 0;">🟣 NEWS2 ≥ 9 — APPEL DÉCHOCAGE IMMÉDIAT</div>')
        elif _n2 >= 7:
            H('<div style="background:#7F1D1D;color:#FEE2E2;border-radius:8px;padding:10px;text-align:center;font-weight:800;font-size:.9rem;margin:6px 0;">🔴 NEWS2 ≥ 7 — APPEL MÉDICAL IMMÉDIAT</div>')

        # Vitaux en grille visuelle colorée
        def _vcss(v, lo, hi):
            return "crit" if (v < lo or v > hi) else ("warn" if (v < lo*1.08 or v > hi*0.93) else "")
        H(f'<div class="vg6">'
          f'<div class="vbox {_vcss(SS.v_fc,60,100)}"><div class="vbox-lbl">FC</div><div class="vbox-val">{SS.v_fc}</div></div>'
          f'<div class="vbox {_vcss(SS.v_pas,90,140)}"><div class="vbox-lbl">PAS</div><div class="vbox-val">{SS.v_pas}</div></div>'
          f'<div class="vbox {_vcss(SS.v_spo2,94,100)}"><div class="vbox-lbl">SpO₂%</div><div class="vbox-val">{SS.v_spo2}</div></div>'
          f'<div class="vbox {_vcss(SS.v_fr,12,20)}"><div class="vbox-lbl">FR</div><div class="vbox-val">{SS.v_fr}</div></div>'
          f'<div class="vbox {_vcss(SS.v_temp,36.0,38.0)}"><div class="vbox-lbl">T°C</div><div class="vbox-val">{SS.v_temp:.1f}</div></div>'
          f'<div class="vbox {_vcss(SS.v_gcs,14,15)}"><div class="vbox-lbl">GCS</div><div class="vbox-val">{SS.v_gcs}</div></div>'
          f'</div>')

        _si_val = round(SS.v_fc / max(1, SS.v_pas), 2)
        if _si_val >= 1.5:
            AL(f"Shock Index {_si_val} ≥ 1.5 — CHOC DÉCOMPENSÉ", "danger")
        elif _si_val >= 1.0:
            AL(f"Shock Index {_si_val} ≥ 1.0 — Instabilité hémodynamique", "warning")
        else:
            st.caption(f"Shock Index : {_si_val} — Stable")

        if age < 18:
            _sv, _stxt, _salerte = sipa(SS.v_fc, age)
            AL(_stxt, "danger" if _salerte else "success")

        st.divider()

        # ── BLOC C : Douleur EVA — tactile large ───────────────────────────────
        H('<div class="card-title">😣 Douleur (EVA / NRS)</div>')
        _eva_key = WK("tr_eva")
        if _eva_key not in SS:
            SS[_eva_key] = str(int(SS.eva or 0))

        _eva_raw = st.select_slider(
            "Intensité douloureuse",
            options=[str(i) for i in range(11)],
            value=SS[_eva_key],
            key=_eva_key,
        )
        SS.eva = int(_eva_raw)
        EVA_BAR(SS.eva)

        if SS.eva >= 8:
            AL(f"EVA {SS.eva}/10 — Douleur sévère — Antalgie forte requise (piritramide / morphine)", "danger")
        elif SS.eva >= 5:
            AL(f"EVA {SS.eva}/10 — Antalgie palier 2-3 à initier", "warning")
        elif SS.eva >= 2:
            AL(f"EVA {SS.eva}/10 — Antalgie palier 1 (paracétamol)", "info")

        st.divider()

        # ── BLOC D : Glycémie capillaire ───────────────────────────────────────
        H('<div class="card-title">🩸 Glycémie capillaire</div>')
        _gl_raw = st.number_input("mg/dl (0 = non mesuré)", 0, 800, 0, 5, key="tr_gl",
                                   label_visibility="collapsed")
        if _gl_raw > 0:
            SS.gl = float(_gl_raw)
            _mm = round(_gl_raw / 18.016, 1)
            st.caption(f"→ {_mm} mmol/l")
            if _gl_raw < 54:
                AL(f"HYPOGLYCÉMIE SÉVÈRE {_gl_raw} mg/dl — Glucose 30 % IV IMMÉDIAT", "danger")
            elif _gl_raw < 70:
                AL(f"Hypoglycémie modérée {_gl_raw} mg/dl — Correction urgente", "warning")
            elif _gl_raw > 360:
                AL(f"Hyperglycémie sévère {_gl_raw} mg/dl — Bilan acidocétose", "danger")
            elif _gl_raw > 180:
                AL(f"Hyperglycémie {_gl_raw} mg/dl", "info")

        st.divider()

        # ── BLOC E : Motif + critères FRENCH ──────────────────────────────────
        H('<div class="card-title">🏷️ Motif de recours</div>')
        _cat  = st.selectbox("Catégorie", list(MOTS_CAT.keys()), key="tr_cat")
        _mot  = st.selectbox("Motif principal", MOTS_CAT[_cat], key="tr_mot")
        SS.cat   = _cat
        SS.motif = _mot

        # Drapeaux rouges spécifiques au motif
        _det = dict(SS.det) if isinstance(SS.det, dict) else {}
        _det.update({"eva": SS.eva, "atcd": atcd, "glycemie_mgdl": SS.gl})

        _purpura_chk = st.checkbox("🔴 Purpura / pétéchies NON effaçables (test du verre)", key=WK("tr_pur"))
        _det["purpura"] = _purpura_chk
        if _purpura_chk:
            H('<div style="background:#7F1D1D;color:#FEE2E2;border-radius:10px;padding:14px;font-weight:700;margin:8px 0;animation:pulse 2s infinite;">'
              '🔴 PURPURA FULMINANS SUSPECTÉ — Ceftriaxone 2 g IV IMMÉDIAT — NE PAS ATTENDRE'
              '</div>')

        # ── Discriminants enrichis (questions bool/select/number) ─────────────
        _disc_answers = {}
        if SS.motif in DISCRIMINANTS_ENRICHIS:
            H('<div class="card-title" style="margin-top:10px;">🔍 Critères discriminants FRENCH</div>')
            _disc_answers = render_discriminants_enrichis(SS.motif, key_prefix=WK("tr_disc"))
            # Intégrer les réponses dans det immédiatement
            _det_updates = process_answers(SS.motif, _disc_answers)
            _det.update(_det_updates)

        # Discriminant FRENCH simplifié (sélecteur de niveau) si pas de discriminants enrichis
        _proto = get_protocol(SS.motif)
        if _proto and _proto.get("criteria") and SS.motif not in DISCRIMINANTS_ENRICHIS:
            _selected_crit = render_discriminants(SS.motif, key=WK("tr_disc2"))
        else:
            _selected_crit = None

        SS.det = _det

        st.divider()

        # ── BLOC F : CALCUL DU TRIAGE (bouton proéminent) ─────────────────────
        if st.button("⚡ CALCULER LE TRIAGE", type="primary", use_container_width=True, key="tr_calc"):
            SS.v_news2 = _n2
            SS.niv, SS.just, SS.crit = french_triage(
                SS.motif, SS.det, SS.v_fc, SS.v_pas, SS.v_spo2,
                SS.v_fr, SS.v_gcs, SS.v_temp, age, SS.v_news2, SS.gl,
            )
            if _selected_crit:
                SS.niv, SS.just, SS.crit = apply_discriminant_selection(
                    SS.niv, SS.just, SS.crit, _selected_crit)

        # ── RÉSULTAT — toujours visible si calculé ────────────────────────────
        if SS.niv:
            _css = TCSS.get(SS.niv, "tri-3B")
            _lbl = LABELS.get(SS.niv, f"TRI {SS.niv}")
            _sec = SECTEURS.get(SS.niv, "À définir")
            _del = DELAIS.get(SS.niv, 60)
            H(f'<div class="tri-hero {_css}">'
              f'<div class="tri-hero-level">{_lbl}</div>'
              f'<div class="tri-hero-just">{SS.just}</div>'
              f'<div class="tri-hero-meta">'
              f'<span class="tri-meta-chip">📍 {_sec}</span>'
              f'<span class="tri-meta-chip">⏱ Délai ≤ {_del} min</span>'
              f'<span class="tri-meta-chip">NEWS2 {SS.v_news2}</span>'
              f'</div></div>')

            # Alertes transversales
            _D, _A = verifier_coherence(
                SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr,
                SS.v_gcs, SS.v_temp, SS.eva, SS.motif,
                atcd, SS.det, SS.v_news2, SS.gl)
            for d in _D: AL(d, "danger")
            for a in _A: AL(a, "warning")

            st.divider()

            # ── Synthèse IAO copy-pasteable ────────────────────────────────────
            _si_txt  = f"{_si_val}"
            _gl_txt  = f"{SS.gl:.0f} mg/dl ({SS.gl/18.016:.1f} mmol/l)" if SS.gl else "Non mesurée"
            _atcd_txt = ", ".join(atcd) if atcd else "Aucun"
            _now_txt  = datetime.now().strftime("%d/%m/%Y à %H:%M")
            _synt = (
                f"SYNTHÈSE IAO — {_now_txt}\n"
                f"Op. : {SS.op or 'IAO'} | Session : {SS.uid_cur or '—'}\n"
                f"{'═'*50}\n"
                f"TRIAGE  : {SS.niv} — {_lbl}\n"
                f"Raison  : {SS.just}\n"
                f"Secteur : {_sec} | Délai médecin ≤ {_del} min\n"
                f"Motif   : {SS.motif} ({SS.cat})\n"
                f"EVA     : {SS.eva}/10\n"
                f"{'─'*50}\n"
                f"FC {SS.v_fc} | PAS {SS.v_pas} | SpO2 {SS.v_spo2}%\n"
                f"FR {SS.v_fr} | T° {SS.v_temp}°C | GCS {SS.v_gcs}/15\n"
                f"Shock Index {_si_txt} | NEWS2 {SS.v_news2}\n"
                f"Glycémie : {_gl_txt}\n"
                f"{'─'*50}\n"
                f"ATCD   : {_atcd_txt}\n"
                f"Allergie: {alg or 'aucune'}\n"
                f"O₂     : {'OUI' if o2 else 'Non'}\n"
                f"{'═'*50}\n"
                f"FRENCH V1.1 | BCFI Belgique — Ismail Ibn-Daifa — AKIR-IAO v19.0"
            )

            with st.expander("📋 Synthèse IAO — Copier / Télécharger", expanded=False):
                st.code(_synt, language=None)
                st.download_button("📥 Télécharger (.txt)", data=_synt,
                    file_name=f"IAO_{datetime.now().strftime('%Y%m%d_%H%M')}_Tri{SS.niv}.txt",
                    mime="text/plain", use_container_width=True)

            # ── Enregistrer + SBAR rapide ──────────────────────────────────────
            _sv1, _sv2 = st.columns(2)
            if _sv1.button("💾 Enregistrer patient", use_container_width=True, key="tr_save"):
                _uid = enregistrer_patient({
                    "motif": SS.motif, "cat": SS.cat, "niv": SS.niv,
                    "n2": SS.v_news2, "fc": SS.v_fc, "pas": SS.v_pas,
                    "spo2": SS.v_spo2, "fr": SS.v_fr, "temp": SS.v_temp,
                    "gcs": SS.v_gcs, "op": SS.op,
                })
                SS.uid_cur = _uid; SS.t_reev = datetime.now()
                SS.histo.insert(0, {"uid": _uid, "h": datetime.now().strftime("%H:%M"),
                                     "motif": SS.motif, "niv": SS.niv, "n2": SS.v_news2})
                st.success(f"✅ Enregistré — UID : {_uid}")

            if _sv2.button("📡 SBAR rapide", use_container_width=True, key="tr_sbar"):
                SS["show_sbar"] = True

            if SS.get("show_sbar"):
                _sbar = build_sbar(age, SS.motif, SS.cat, atcd, alg, o2,
                    SS.v_temp, SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr, SS.v_gcs,
                    SS.eva, SS.v_news2, SS.niv, SS.just, SS.crit,
                    SS.op or "IAO", SS.gl)
                SBAR_RENDER(_sbar)

        DISC()


    # ═══════════════════════════════════════════════════════════════════════════
    # ONGLET 2 — PHARMACIE (filtrée par motif, doses calculées)
    # ═══════════════════════════════════════════════════════════════════════════
    with T[2]:
        _gl_ph = (SS.det.get("glycemie_mgdl") if isinstance(SS.det, dict) else None) or SS.gl
        _dose_mode = "mg/kg" if age < 15 else "adulte"

        # Bandeau patient + alertes critiques
        H(f'<div style="background:linear-gradient(135deg,#004A99,#0069D9);color:#fff;'
          f'border-radius:10px;padding:10px 14px;margin-bottom:10px;display:flex;'
          f'justify-content:space-between;align-items:center;">'
          f'<div><div style="font-size:.65rem;opacity:.75;">Doses pour</div>'
          f'<div style="font-size:1.1rem;font-weight:800;">{poids:.0f} kg — {age:.0f} ans'
          f' <span style="font-size:.75rem;opacity:.7;">({_dose_mode})</span></div></div>'
          f'<div style="text-align:right;font-size:.7rem;opacity:.8;">'
          f'{"⚠️ " + str(len([a for a in [_trt_checks.get("IMAO (inhibiteurs MAO)"), atcd_checks.get("Insuffisance rénale chronique"), trt_checks.get("Anticoagulants/AOD")] if a])) + " alerte(s)" if any([_trt_checks.get("IMAO (inhibiteurs MAO)"), atcd_checks.get("Insuffisance rénale chronique"), trt_checks.get("Anticoagulants/AOD")]) else "✅ Pas d'alerte PV"}'
          f'</div></div>')

        # Alertes PV critiques en haut
        if _trt_checks.get("IMAO (inhibiteurs MAO)"):
            H('<div class="pharma-alert-bar">🔴 IMAO — Tramadol CONTRE-INDIQUÉ ABSOLU</div>')
        if atcd_checks.get("Insuffisance rénale chronique"):
            H('<div class="pharma-alert-bar">🔴 Insuff. rénale — AINS tous CONTRE-INDIQUÉS</div>')
        if _trt_checks.get("Anticoagulants/AOD"):
            AL("Anticoagulants en cours — Vigilance hémorragique renforcée", "warning")
        if SS.niv in ("M", "1", "2") and SS.eva >= 7:
            H(f'<div style="background:#78350F;color:#FDE68A;border-radius:8px;padding:10px;font-weight:700;margin:6px 0;">'
              f'⚠️ TRI {SS.niv} — EVA {SS.eva}/10 — ANTALGIE FORTE PRIORITAIRE (piritramide/morphine)</div>')

        # ── Raccourcis médicaments (boutons rapides) ───────────────────────────
        H('<div class="card-title">⚡ Raccourcis — Doses immédiates</div>')
        _rq1, _rq2, _rq3, _rq4, _rq5, _rq6 = st.columns(6)
        for _col, _name, _fn, _args in [
            (_rq1, "Para IV",     paracetamol,  (poids, age, atcd)),
            (_rq2, "Adrénaline",  adrenaline,   (poids, atcd)),
            (_rq3, "Ceftriaxone", ceftriaxone,  (poids, age, atcd)),
            (_rq4, "Morphine",    morphine,      (poids, age, atcd)),
            (_rq5, "Ondansétron", ondansetron,  (poids, age, atcd)),
            (_rq6, "Naloxone",    naloxone,     (poids, age, False, atcd)),
        ]:
            if _col.button(_name, key=WK(f"rq_{_name}"), use_container_width=True):
                _rx, _re = _fn(*_args)
                if _re: AL(_re, "danger")
                elif _rx:
                    # Afficher la dose clé selon le médicament
                    _dose_txt = (
                        f"{_rx.get('dose_g',_rx.get('dose_mg',_rx.get('dose','?')))} — {_rx.get('admin',_rx.get('voie',''))}"
                    )
                    st.toast(f"✅ {_name} : {_dose_txt}", icon="💊")

        # ── Protocoles IAO anticipés (selon motif actif) ──────────────────────
        if SS.motif and SS.motif in PROTOCOLES_IAO:
            st.divider()
            H(f'<div class="card-title">🚑 Protocoles anticipés IAO — {SS.motif}</div>')
            for _proto_iao in PROTOCOLES_IAO[SS.motif]:
                _cond = _proto_iao.get("condition", lambda v: True)
                try:
                    _show = _cond({"pas": SS.v_pas, "spo2": SS.v_spo2, "fc": SS.v_fc})
                except Exception:
                    _show = True
                if not _show:
                    continue
                _dose_iao = _proto_iao.get("dose") or ""
                if not _dose_iao and _proto_iao.get("dose_fn"):
                    try: _dose_iao = _proto_iao["dose_fn"](poids)
                    except Exception: _dose_iao = "?"
                AL(f"{_proto_iao['med']} : {_dose_iao} ({_proto_iao.get('voie','?')})", "info")

        # ── Vérifications sécurité croisées pour médicaments courants ─────────
        for _med_chk in ["Tramadol", "Morphine", "AINS", "Midazolam"]:
            for _sa in check_safety(_med_chk, {"atcd": atcd}, {"age": age, "poids": poids}):
                AL(_sa["message"], _sa["niveau"])

        st.divider()

        # ── Filtre par catégorie ───────────────────────────────────────────────
        _PH = st.tabs(["Antalgiques", "Urgences vitales", "Infectiologie", "Cardio/Respi", "Pédiatrie", "🧪 Perfusions IV"])

        # ── Antalgiques ───────────────────────────────────────────────────────
        with _PH[0]:
            # Palier 1
            H('<div class="card-title">Palier 1 — Non opioïdes</div>')
            _pc1, _pc2 = st.columns(2)

            with _pc1:
                _p, _pe = paracetamol(poids, age, atcd)
                if _pe: AL(_pe, "danger")
                else:
                    _dose_p = (_p or {}).get("dose_display", f"{(_p or {}).get('dose_mg',1000):.0f} mg")
                    H(f'<div class="rx-compact"><div class="rx-compact-dose">{_dose_p}</div>'
                      f'<div class="rx-compact-info"><div class="rx-compact-name">Paracétamol IV (Perfalgan)</div>'
                      f'<div class="rx-compact-detail">{(_p or {}).get("admin","")} — {(_p or {}).get("note","")}</div>'
                      f'<div class="rx-compact-detail" style="color:#64748B;font-style:italic;">{(_p or {}).get("ref","")}</div></div></div>')

            with _pc2:
                _n, _ne = naproxene(poids, age, atcd)
                if _ne: H(f'<div class="rx-compact"><div class="rx-compact-dose" style="color:#EF4444;">🔒</div>'
                           f'<div class="rx-compact-info"><div class="rx-compact-name">Naproxène PO</div>'
                           f'<div class="rx-compact-detail" style="color:#EF4444;">{_ne}</div></div></div>')
                else:
                    H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_n or {}).get("dose_mg",500):.0f} mg</div>'
                      f'<div class="rx-compact-info"><div class="rx-compact-name">Naproxène PO</div>'
                      f'<div class="rx-compact-detail">{(_n or {}).get("admin","")} — {(_n or {}).get("note","")}</div></div></div>')

            _pc3, _pc4 = st.columns(2)
            with _pc3:
                _k, _ke = ketorolac(poids, age, atcd)
                if _ke: H(f'<div class="rx-compact"><div class="rx-compact-dose" style="color:#EF4444;">🔒</div>'
                           f'<div class="rx-compact-info"><div class="rx-compact-name">Taradyl® IM</div>'
                           f'<div class="rx-compact-detail" style="color:#EF4444;">{_ke}</div></div></div>')
                else:
                    H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_k or {}).get("dose_mg",30):.0f} mg IM</div>'
                      f'<div class="rx-compact-info"><div class="rx-compact-name">Taradyl® (Kétorolac) IM</div>'
                      f'<div class="rx-compact-detail">{(_k or {}).get("admin","")} — {(_k or {}).get("note","")}</div></div></div>')

            with _pc4:
                _d, _de = diclofenac(poids, age, atcd)
                if _de: H(f'<div class="rx-compact"><div class="rx-compact-dose" style="color:#EF4444;">🔒</div>'
                           f'<div class="rx-compact-info"><div class="rx-compact-name">Voltarène® IM</div>'
                           f'<div class="rx-compact-detail" style="color:#EF4444;">{_de}</div></div></div>')
                else:
                    H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_d or {}).get("dose_mg",75):.0f} mg IM</div>'
                      f'<div class="rx-compact-info"><div class="rx-compact-name">Voltarène® (Diclofénac) IM</div>'
                      f'<div class="rx-compact-detail">{(_d or {}).get("admin","")} — {(_d or {}).get("note","")}</div></div></div>')

            st.divider()
            H('<div class="card-title">Palier 2 — Opioïdes faibles</div>')
            _tr, _tre = tramadol(poids, age, atcd)
            if _tre: AL(_tre, "danger" if "contre" in _tre.lower() else "warning")
            else:
                H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_tr or {}).get("dose_mg",50):.0f} mg</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Tramadol (Tradonal®)</div>'
                  f'<div class="rx-compact-detail">{(_tr or {}).get("admin","")} — {(_tr or {}).get("note","")}</div></div></div>')

            st.divider()
            H('<div class="card-title">Palier 3 — Opioïdes forts</div>')
            _di, _die = piritramide(poids, age, atcd)
            if not _die:
                for _ma, _mc in (_di or {}).get("alerts",[]): AL(_ma, _mc)
                H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_di or {}).get("dose_min",0):.1f}–{(_di or {}).get("dose_max",0):.1f} mg IV</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Dipidolor® (Piritramide) IV</div>'
                  f'<div class="rx-compact-detail">{(_di or {}).get("admin","")} — {(_di or {}).get("note","")}</div></div></div>')
            _mo, _moe = morphine(poids, age, atcd)
            if not _moe:
                for _ma, _mc in (_mo or {}).get("alerts",[]): AL(_ma, _mc)
                H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_mo or {}).get("dose_min",0):.1f}–{(_mo or {}).get("dose_max",0):.1f} mg IV</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Morphine IV titrée</div>'
                  f'<div class="rx-compact-detail">{(_mo or {}).get("admin","")} — {(_mo or {}).get("note","")}</div></div></div>')

            st.divider()
            H('<div class="card-title">Antispasmodique</div>')
            _li, _lie = litican(poids, age, atcd)
            if not _lie:
                H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_li or {}).get("dose_mg",40):.0f} mg IM</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Litican® IM (Tiémonium)</div>'
                  f'<div class="rx-compact-detail">{(_li or {}).get("voie","")} — {(_li or {}).get("dose_note","")}</div></div></div>')

        # ── Urgences vitales ──────────────────────────────────────────────────
        with _PH[1]:
            H('<div class="card-title">Urgences vitales — Doses immédiates</div>')

            _ar, _are = adrenaline(poids, atcd)
            if not _are:
                H(f'<div class="rx-compact urgent"><div class="rx-compact-dose">{(_ar or {}).get("dose_mg",0.5)} mg IM</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Adrénaline IM (Sterop 1 mg/ml)</div>'
                  f'<div class="rx-compact-detail">{(_ar or {}).get("voie","")} — {(_ar or {}).get("rep","")}</div></div></div>')

            if _gl_ph is not None:
                _gr, _gre = glucose(poids, _gl_ph, atcd)
                if not _gre:
                    H(f'<div class="rx-compact urgent"><div class="rx-compact-dose">{(_gr or {}).get("dose_g",0)} g IV</div>'
                      f'<div class="rx-compact-info"><div class="rx-compact-name">Glucose 30 % IV</div>'
                      f'<div class="rx-compact-detail">{(_gr or {}).get("vol","")} — {(_gr or {}).get("ctrl","")}</div></div></div>')
            else:
                H('<div class="rx-compact" style="opacity:.5;"><div class="rx-compact-dose">?</div>'
                  '<div class="rx-compact-info"><div class="rx-compact-name">Glucose 30 % IV</div>'
                  '<div class="rx-compact-detail">Mesurer la glycémie d\'abord</div></div></div>')

            _dep_ph = st.checkbox("Patient dépendant aux opioïdes (naloxone titrée)", key=WK("ph_dep2"))
            _nr, _ = naloxone(poids, age, _dep_ph, atcd)
            if _nr:
                H(f'<div class="rx-compact urgent"><div class="rx-compact-dose">{(_nr or {}).get("dose",0.4)} mg IV</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Naloxone IV (Narcan®)</div>'
                  f'<div class="rx-compact-detail">{(_nr or {}).get("admin","")}</div></div></div>')

            st.divider()
            H('<div class="card-title">Sepsis bundle 1h (SSC 2021)</div>')
            _sblact = st.number_input("Lactate (mmol/l, 0=non dosé)", 0.0, 20.0, 0.0, 0.1, key="ph_sblact")
            _sb = sepsis_bundle_1h(SS.v_pas or 120, _sblact or None, SS.v_temp, SS.v_fc, poids, atcd) or {}
            if _sb.get("choc_septique"):
                AL("CHOC SEPTIQUE — Réanimation immédiate", "danger")
            for _ml, _md, _mc in _sb.get("checklist", []):
                H(f'<div class="al {_mc}" style="padding:6px 12px;margin:2px 0;">'
                  f'<input type="checkbox" style="margin-right:8px;"><strong>{_ml}</strong> — {_md}</div>')

            st.divider()
            H('<div class="card-title">Acide tranexamique IV</div>')
            H('<div class="rx-compact urgent"><div class="rx-compact-dose">1 g IV</div>'
              '<div class="rx-compact-info"><div class="rx-compact-name">Acide tranexamique (CRASH-2)</div>'
              '<div class="rx-compact-detail">En 10 min — Efficace < 3h post-trauma — puis 1 g/8h</div></div></div>')

        # ── Infectiologie ─────────────────────────────────────────────────────
        with _PH[2]:
            H('<div class="card-title">Antibiotiques urgents</div>')
            _cf, _cfe = ceftriaxone(poids, age, atcd)
            if not _cfe:
                H(f'<div class="rx-compact urgent"><div class="rx-compact-dose">{(_cf or {}).get("dose_g",2)} g IV</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Ceftriaxone IV (Rocéphine®)</div>'
                  f'<div class="rx-compact-detail">{(_cf or {}).get("admin","")} — {(_cf or {}).get("note","")}</div></div></div>')

            st.divider()
            H('<div class="card-title">Crise hypertensive — Cibles par étiologie</div>')
            AL("Ne jamais normaliser trop rapidement — risque ischémique cérébral", "warning")
            _ctx_hta = st.selectbox("Étiologie HTA", [
                "Urgence hypertensive standard", "AVC ischémique (non thrombolysé)",
                "AVC ischémique (si thrombolyse)", "AVC hémorragique",
                "Dissection aortique", "OAP hypertensif",
            ], key="ph_ctx_hta2")
            _chp, _che = crise_hypertensive(SS.v_pas or 120, _ctx_hta, poids, atcd)
            if _che: AL(_che, "danger")
            else:
                AL(f"Cible : {(_chp or {}).get('cible','À confirmer')}", "warning")

        # ── Cardio / Respi ────────────────────────────────────────────────────
        with _PH[3]:
            H('<div class="card-title">Bronchospasme</div>')
            _grav2 = st.select_slider("Gravité bronchospasme", ["legere","moderee","severe"], "moderee",
                key=WK("ph_grav2"),
                format_func=lambda x: {"legere":"Légère","moderee":"Modérée","severe":"Sévère"}[x])
            _sr, _se = salbutamol(poids, age, _grav2, atcd)
            if not _se:
                H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_sr or {}).get("dose_mg",2.5)} mg</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Salbutamol nébulisation (Ventolin®)</div>'
                  f'<div class="rx-compact-detail">{(_sr or {}).get("dilution","")} — {(_sr or {}).get("debit_o2","")}</div></div></div>')

            st.divider()
            H('<div class="card-title">OAP / Diurèse</div>')
            _fu, _fue = furosemide(poids, age, atcd)
            if not _fue:
                H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_fu or {}).get("dose_min",40):.0f}–{(_fu or {}).get("dose_max",80):.0f} mg IV</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Furosémide IV (Lasix®)</div>'
                  f'<div class="rx-compact-detail">IV lent en 2-5 min</div></div></div>')

        # ── Pédiatrie ─────────────────────────────────────────────────────────
        with _PH[4]:
            if age >= 18:
                AL("Cet onglet est réservé aux patients < 18 ans", "info")
            else:
                H(f'<div class="card-title">EME Pédiatrique — {poids:.0f} kg</div>')
                _det_ped = SS.det if isinstance(SS.det, dict) else {}
                _dur_epi  = float(_det_ped.get("duree_min", 0) or 0)
                _encours  = bool(_det_ped.get("en_cours", False))
                _dur_epi_i = st.number_input("Durée de crise (min)", 0.0, 120.0, _dur_epi, 0.5, key="ph_dur_epi")
                _encours_i = st.checkbox("Crise en cours", value=_encours, key="ph_encours_epi")
                _eme = protocole_epilepsie_ped(poids, age, _dur_epi_i, _encours_i, atcd) or {}
                if _eme.get("eme_etabli"):
                    AL(f"EME établi ({_dur_epi_i:.0f} min) — 2e ligne", "danger")
                if _encours_i:
                    AL("Crise EN COURS — anticonvulsivant IMMÉDIAT", "danger")

                _e1, _e2 = st.columns(2)
                for _col, _drug_key, _name in [
                    (_e1, "midazolam_buccal", "Midazolam buccal"),
                    (_e2, "diazepam_rectal",  "Diazépam rectal"),
                    (_e1, "lorazepam_iv",     "Lorazépam IV"),
                    (_e2, "levetiracetam_iv", "Lévétiracétam IV"),
                ]:
                    _d = _eme.get(_drug_key) or {}
                    if _d.get("dose"):
                        with _col:
                            H(f'<div class="rx-compact"><div class="rx-compact-dose" style="font-size:.85rem;">{_d["dose"]}</div>'
                              f'<div class="rx-compact-info"><div class="rx-compact-name">{_name}</div>'
                              f'<div class="rx-compact-detail">{_d.get("note","")}</div></div></div>')

                st.divider()
                H('<div class="card-title">Kétamine intranasale</div>')
                _ki, _kie = ketamine_intranasale(poids, age, atcd)
                if _kie: AL(_kie, "warning")
                else:
                    H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_ki or {}).get("dose_mg",0):.0f} mg IN</div>'
                      f'<div class="rx-compact-info"><div class="rx-compact-name">Kétamine intranasale</div>'
                      f'<div class="rx-compact-detail">{(_ki or {}).get("admin","")} — Onset {(_ki or {}).get("onset","")}</div></div></div>')

                st.divider()
                H('<div class="card-title">Midazolam IM / IN (Hypnovel® 5 mg/ml)</div>')
                _mi_im, _mi_im_err = midazolam_im(poids, age, atcd)
                if _mi_im_err: AL(_mi_im_err, "danger")
                else:
                    for _ma, _mc in (_mi_im or {}).get("alerts", []): AL(_ma, _mc)
                    H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_mi_im or {}).get("dose_mg",0):.1f} mg ({(_mi_im or {}).get("volume_ml",0):.2f} ml)</div>'
                      f'<div class="rx-compact-info"><div class="rx-compact-name">Midazolam IM/IN (Hypnovel® 5 mg/ml)</div>'
                      f'<div class="rx-compact-detail">{(_mi_im or {}).get("admin","")}</div>'
                      f'<div class="rx-compact-detail" style="color:#64748B;">Onset : {(_mi_im or {}).get("onset","")}</div></div></div>')

        # ── Générateur d'étiquette PSE ─────────────────────────────────────────
        st.divider()
        with st.expander("🏷️ Générateur d'étiquette PSE — traçabilité seringue", expanded=False):
            st.caption("Compatible AR 78 AFMPS 2019 — Identification seringue auto-pousseuse")
            _eq1, _eq2, _eq3 = st.columns(3)
            _eq_med   = _eq1.text_input("Médicament", value="Morphine",   key=WK("eq_med"))
            _eq_conc  = _eq2.number_input("Concentration (mg/ml)", 0.01, 50.0, 1.0, 0.1, key="eq_conc")
            _eq_vol   = _eq3.number_input("Volume total (ml)", 10, 100, 50, key="eq_vol")
            _eq4, _eq5 = st.columns(2)
            _eq_debit = _eq4.number_input("Débit PSE (ml/h)", 0.1, 100.0, 5.0, 0.5, key="eq_debit")
            _eq_op    = _eq5.text_input("Opérateur", value=SS.op or "IAO", key="eq_op")
            if _eq_debit and _eq_conc:
                _eq_txt = generer_etiquette(
                    medicament=_eq_med, concentration=_eq_conc,
                    debit_mlh=_eq_debit, vol_total=_eq_vol,
                    poids=poids, operateur=_eq_op or "IAO",
                )
                st.code(_eq_txt, language=None)
                import datetime as _dt
                st.download_button("🖨️ Télécharger (.txt)", data=_eq_txt,
                    file_name=f"etiq_{_eq_med}_{_dt.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain", use_container_width=True)

        # ─────────────────────────────────────────────────────────────────────
        # _PH[5] — CALCUL DE PERFUSIONS IV
        # ─────────────────────────────────────────────────────────────────────
        with _PH[5]:
            H(f'''<div style="background:linear-gradient(135deg,#0F172A,#1E3A5F);color:#fff;
                border-radius:10px;padding:12px 16px;margin-bottom:12px;">
              <div style="font-size:.65rem;opacity:.75;text-transform:uppercase;letter-spacing:.1em;">Calcul perfusion</div>
              <div style="font-size:1.05rem;font-weight:800;">Patient : {poids:.0f} kg</div>
              <div style="font-size:.72rem;opacity:.75;margin-top:2px;">Concentrations standard Hainaut — BCFI Belgique</div>
            </div>''')

            # ── Aide-mémoire rapide ────────────────────────────────────────────
            st.markdown("**Choisir la perfusion à calculer :**")
            _perf_choice = st.selectbox("Médicament / Indication", [
                "— Sélectionner —",
                "Morphine PSE — Analgésie IV continue",
                "Dipidolor® PSE — Analgésie IV continue",
                "Kétamine PSE — Analgésie subanesthésique",
                "Midazolam PSE — Sédation / Convulsion",
                "Adrénaline IV — Anaphylaxie / Choc",
                "Noradrénaline IV — Choc septique (SSC 2021)",
                "Dobutamine IV — Choc cardiogénique",
                "Amiodarone IV — FA / TV stable",
                "Labétalol IV — HTA sévère / Dissection",
                "Nicardipine IV — HTA sévère (alternative)",
                "Magnésium IV — Pré-éclampsie / Torsades",
                "Insuline rapide IV — Acidocétose / Hyperglycémie",
                "🔢 Convertisseur débit ↔ dose",
            ], key="perf_choice")

            def _rx_perf(p: dict) -> None:
                """Affiche un résultat de perfusion de façon standardisée."""
                if not p:
                    return
                _details_html = ""
                if p.get("details"):
                    _items = "".join(f'<div style="font-size:.72rem;color:#94A3B8;margin:2px 0;">• {d}</div>' for d in p["details"])
                    _details_html = f'<div style="border-top:1px solid #1E293B;margin-top:10px;padding-top:8px;">{_items}</div>'
                H(f'''<div style="background:#0F172A;border:1.5px solid #334155;border-radius:10px;padding:14px 18px;margin:10px 0;">
                  <div style="font-size:.65rem;color:#64748B;text-transform:uppercase;letter-spacing:.1em;">{p.get("label","")}</div>
                  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px;">
                    <div style="text-align:center;">
                      <div style="font-size:2rem;font-weight:900;color:#38BDF8;font-family:\'IBM Plex Mono\',monospace;">{p.get("debit_mlh",0)}</div>
                      <div style="font-size:.65rem;color:#64748B;">ml/h</div></div>
                    <div style="text-align:center;">
                      <div style="font-size:2rem;font-weight:900;color:#A78BFA;font-family:\'IBM Plex Mono\',monospace;">{int(p.get("gttes_min",0))}</div>
                      <div style="font-size:.65rem;color:#64748B;">gttes/min</div></div>
                    <div style="text-align:center;">
                      <div style="font-size:1.3rem;font-weight:900;color:#4ADE80;font-family:\'IBM Plex Mono\',monospace;">{p.get("conc_mgml",0)}</div>
                      <div style="font-size:.65rem;color:#64748B;">mg/ml</div></div>
                  </div>
                  <div style="border-top:1px solid #1E293B;margin-top:12px;padding-top:10px;">
                    <div style="font-size:.7rem;color:#94A3B8;margin-bottom:6px;font-weight:600;">DILUTION :</div>
                    <div style="font-size:.75rem;color:#CBD5E1;">{p.get("dilution","")}</div>
                  </div>
                  {_details_html}
                  <div style="font-size:.6rem;color:#475569;margin-top:8px;font-style:italic;">{p.get("ref","")}</div>
                </div>''')
                for _am, _ac in p.get("alerts", []):
                    AL(_am, _ac)
                if p.get('duree_h', 0) > 0:
                    _dur_txt = f"Durée d'autonomie : ≈ {p['duree_h']:.1f} h ({p['vol_total_ml']:.0f} ml à {p['debit_mlh']:.1f} ml/h)"
                    st.caption(_dur_txt)
            # ── Rendu selon sélection ─────────────────────────────────────────
            if _perf_choice == "Morphine PSE — Analgésie IV continue":
                _pc1, _pc2 = st.columns(2)
                _mo_dose = _pc1.number_input("Dose µg/kg/h", 5.0, 80.0, 20.0, 5.0, key="pm_dose")
                _mo_vol  = _pc2.selectbox("Volume seringue (ml)", [20, 50], index=1, key="pm_vol")
                _rx_perf(perf_morphine(poids, _mo_dose, _mo_vol, atcd))

            elif _perf_choice == "Dipidolor® PSE — Analgésie IV continue":
                _pc1, _pc2 = st.columns(2)
                _pi_dose = _pc1.number_input("Dose µg/kg/h", 5.0, 60.0, 15.0, 5.0, key="pp_dose")
                _pi_vol  = _pc2.selectbox("Volume seringue (ml)", [20, 50], index=1, key="pp_vol")
                _rx_perf(perf_piritramide(poids, _pi_dose, _pi_vol, atcd))

            elif _perf_choice == "Kétamine PSE — Analgésie subanesthésique":
                _ke_ind = st.radio("Indication", ["analgesie","sedation"],
                    format_func=lambda x: {"analgesie":"Analgésie (0,1-0,5 mg/kg/h)", "sedation":"Sédation légère (0,5-2 mg/kg/h)"}[x],
                    horizontal=True, key="pke_ind")
                _rx_perf(perf_ketamine(poids, _ke_ind, atcd))

            elif _perf_choice == "Midazolam PSE — Sédation / Convulsion":
                _mi_ind = st.radio("Indication", ["sedation","convulsion","anxiolyse"],
                    format_func=lambda x: {"sedation":"Sédation","convulsion":"Convulsion","anxiolyse":"Anxiolyse"}[x],
                    horizontal=True, key="pmi_ind")
                _rx_perf(perf_midazolam(poids, _mi_ind, atcd))

            elif _perf_choice == "Adrénaline IV — Anaphylaxie / Choc":
                _ae_ind = st.radio("Indication", ["anaphylaxie","choc_septique"],
                    format_func=lambda x: {"anaphylaxie":"Anaphylaxie sévère","choc_septique":"Choc vasoplégique"}[x],
                    horizontal=True, key="pae_ind")
                _rx_perf(perf_adrenaline(poids, _ae_ind, atcd))

            elif _perf_choice == "Noradrénaline IV — Choc septique (SSC 2021)":
                _na_dose = st.number_input("Dose initiale µg/kg/min", 0.05, 3.0, 0.1, 0.05, key="pna_dose")
                _rx_perf(perf_noradrenaline(poids, _na_dose, atcd))

            elif _perf_choice == "Dobutamine IV — Choc cardiogénique":
                _db_dose = st.number_input("Dose µg/kg/min", 2.0, 20.0, 5.0, 2.5, key="pdb_dose")
                _rx_perf(perf_dobutamine(poids, _db_dose, atcd))

            elif _perf_choice == "Amiodarone IV — FA / TV stable":
                _am_ind = st.radio("Indication", ["fa","tv_stable","choc_refractaire"],
                    format_func=lambda x: {"fa":"FA récente","tv_stable":"TV hémostable","choc_refractaire":"ACR / FV réfractaire"}[x],
                    horizontal=True, key="pam_ind")
                _rx_perf(perf_amiodarone(poids, _am_ind, atcd))

            elif _perf_choice == "Labétalol IV — HTA sévère / Dissection":
                _lb_ctx = st.selectbox("Contexte", ["hta_severe","dissection_aortique"], key="plb_ctx",
                    format_func=lambda x: {"hta_severe":"HTA sévère","dissection_aortique":"Dissection aortique (cible < 120)"}[x])
                _rx_perf(perf_labetalol(poids, _lb_ctx, atcd))

            elif _perf_choice == "Nicardipine IV — HTA sévère (alternative)":
                _rx_perf(perf_nicardipine(poids, atcd))

            elif _perf_choice == "Magnésium IV — Pré-éclampsie / Torsades":
                _mg_ind = st.radio("Indication", ["eclampsia","torsades","asthme"],
                    format_func=lambda x: {"eclampsia":"Pré-éclampsie","torsades":"Torsades de pointes","asthme":"Asthme sévère réfractaire"}[x],
                    horizontal=True, key="pmg_ind")
                _rx_perf(perf_magnesium(poids, _mg_ind, atcd))

            elif _perf_choice == "Insuline rapide IV — Acidocétose / Hyperglycémie":
                _in_ind = st.radio("Indication", ["acidocetose","hyperkaliemie","hyperglycemie"],
                    format_func=lambda x: {"acidocetose":"Acidocétose","hyperkaliemie":"Hyperkaliémie","hyperglycemie":"Hyperglycémie"}[x],
                    horizontal=True, key="pin_ind")
                _in_gl = float(SS.gl or 300)
                _rx_perf(perf_insuline(poids, _in_ind, _in_gl, atcd))

            elif _perf_choice == "🔢 Convertisseur débit ↔ dose":
                st.markdown("##### Convertisseur universel ml/h ↔ dose")
                _cv_c1, _cv_c2 = st.columns(2)
                _cv_conc  = _cv_c1.number_input("Concentration (mg/ml)", 0.001, 50.0, 1.0, 0.1, key="cv_conc")
                _cv_poids = _cv_c2.number_input("Poids (kg)", 1.0, 200.0, float(poids), 1.0, key="cv_poids")

                st.markdown("**→ Débit → Dose :**")
                _cv_debit = st.number_input("Débit connu (ml/h)", 0.1, 500.0, 10.0, 0.5, key="cv_debit")
                _cv_res = convertir_debit(_cv_debit, _cv_conc, _cv_poids)
                H(f'''<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:12px;margin:6px 0;">
                  <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;">
                    <div><div style="font-size:.6rem;color:#64748B;">Dose mg/h</div>
                      <div style="font-size:1.1rem;font-weight:700;color:#004A99;">{_cv_res["dose_mg_h"]:.3f} mg/h</div></div>
                    <div><div style="font-size:.6rem;color:#64748B;">mg/kg/h</div>
                      <div style="font-size:1.1rem;font-weight:700;color:#004A99;">{_cv_res["dose_mg_kg_h"]:.4f} mg/kg/h</div></div>
                    <div><div style="font-size:.6rem;color:#64748B;">µg/kg/min</div>
                      <div style="font-size:1.1rem;font-weight:700;color:#7C3AED;">{_cv_res["dose_ug_kg_min"]:.3f} µg/kg/min</div></div>
                    <div><div style="font-size:.6rem;color:#64748B;">Gttes/min (20 gttes/ml)</div>
                      <div style="font-size:1.1rem;font-weight:700;color:#16A34A;">{int(_cv_debit*20/60)} gttes/min</div></div>
                  </div>
                </div>''')

                st.markdown("**→ Dose → Débit :**")
                _cv_dose2 = st.number_input("Dose souhaitée (mg/h)", 0.001, 1000.0, 1.0, 0.1, key="cv_dose2")
                _cv_calc  = calculer_debit(_cv_dose2, _cv_conc)
                H(f'''<div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;padding:12px;margin:6px 0;">
                  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
                    <div><div style="font-size:.6rem;color:#166534;">Débit ml/h</div>
                      <div style="font-size:1.3rem;font-weight:800;color:#166534;">{_cv_calc["debit_mlh"]:.1f} ml/h</div></div>
                    <div><div style="font-size:.6rem;color:#166534;">Gttes/min adulte (×20)</div>
                      <div style="font-size:1.3rem;font-weight:800;color:#166534;">{int(_cv_calc["gttes_min_adulte"])} gttes/min</div></div>
                    <div><div style="font-size:.6rem;color:#166534;">Microgottes/min (×60)</div>
                      <div style="font-size:1.3rem;font-weight:800;color:#166534;">{int(_cv_calc["gttes_min_ped"])} µgttes/min</div></div>
                  </div>
                </div>''')

        DISC()


    # ═══════════════════════════════════════════════════════════════════════════
    # ONGLET 3 — SCORES CLINIQUES
    # ═══════════════════════════════════════════════════════════════════════════
    with T[3]:
        _SC = st.tabs(["Cardio / Neuro", "Infectio / Respi", "Imagerie"])

        with _SC[0]:
            _sl, _sr = st.columns(2)
            with _sl:
                CARD("qSOFA — Sepsis", "")
                _qs = calculer_qsofa(SS.v_fr or 16, SS.v_gcs or 15, SS.v_pas or 120)
                _qsv = _qs.get("score_val") or 0
                AL(_qs.get("interpretation",""), "danger" if _qsv >= 2 else "warning" if _qsv == 1 else "success")
                AL(_qs.get("recommendation",""), "info")
                CARD_END()

                CARD("BE-FAST — AVC", "")
                _f1, _f2 = st.columns(2)
                _bf_ba = _f1.checkbox("Balance", key=WK("bf_b"))
                _bf_ey = _f2.checkbox("Eyes",    key=WK("bf_e"))
                _bf_fa = _f1.checkbox("Face",    key=WK("bf_f"))
                _bf_ar = _f2.checkbox("Arm",     key=WK("bf_a"))
                _bf_sp = _f1.checkbox("Speech",  key=WK("bf_sp"))
                _bf_ti = _f2.text_input("Vu bien à", key="bf_t", placeholder="14:30")
                _bf = evaluer_fast(_bf_fa, _bf_ar, _bf_sp, _bf_ti, _bf_ba, _bf_ey)
                AL(_bf.get("interpretation",""), "danger" if (_bf.get("score_val") or 0) >= 1 else "success")
                AL(_bf.get("recommendation",""), "info")
                CARD_END()

            with _sr:
                CARD("HEART — Douleur thoracique", "")
                st.caption("Six AJ et al., NHJ 2008")
                _h1, _h2 = st.columns(2)
                _hh = _h1.select_slider("Histoire", [0,1,2], key=WK("ht_h"),
                    format_func=lambda x:{0:"0–Peu évoc.",1:"1–Modéré",2:"2–Très suspect"}[x])
                _he = _h2.select_slider("ECG",     [0,1,2], key=WK("ht_e"),
                    format_func=lambda x:{0:"0–Normal",1:"1–Non spéc.",2:"2–Bloc/STEMI"}[x])
                _ha = _h1.select_slider("Âge",     [0,1,2], key=WK("ht_a"),
                    format_func=lambda x:{0:"0–<45",1:"1–45-65",2:"2–>65"}[x])
                _hr = _h2.select_slider("FRCV",    [0,1,2], key=WK("ht_r"),
                    format_func=lambda x:{0:"0–Aucun",1:"1–1-2",2:"2–≥3"}[x])
                _ht2 = _h1.select_slider("Tropo",  [0,1,2], key=WK("ht_t"),
                    format_func=lambda x:{0:"0–Norm.",1:"1–1-3xN",2:"2–>3xN"}[x])
                _ht = calculer_heart(_hh, _he, _ha, _hr, _ht2)
                _htv = _ht.get("score_val") or 0
                AL(_ht.get("interpretation",""), "danger" if _htv >= 7 else "warning" if _htv >= 4 else "success")
                AL(_ht.get("recommendation",""), "info")
                CARD_END()

                # TIMI contextuel
                if any(k in (SS.motif or "").lower() for k in ("thoracique","sca","coronaire","infarctus")):
                    CARD("TIMI — NSTEMI (motif SCA actif)", "")
                    st.caption("Antman EM et al., JAMA 2000")
                    _ti1, _ti2 = st.columns(2)
                    _tia = _ti1.checkbox("Âge ≥ 65 ans",   key=WK("ti_age"), value=age >= 65)
                    _tif = _ti2.checkbox("≥ 3 FRCV",        key=WK("ti_frcv"))
                    _tis = _ti1.checkbox("Sténose ≥ 50 %",  key=WK("ti_sten"))
                    _tie = _ti2.checkbox("Dév. ST ECG",      key=WK("ti_ecg"))
                    _tin = _ti1.checkbox("≥ 2 angor/24h",   key=WK("ti_ang"))
                    _tiasp = _ti2.checkbox("Aspirine 7j",   key=WK("ti_asp"))
                    _titr = _ti1.checkbox("Marqueurs +",    key=WK("ti_trop"))
                    _tires = calculer_timi(_tia, _tif, _tis, _tie, _tin, _tiasp, _titr)
                    _tisv  = _tires.get("score_val") or 0
                    _ticol = "#EF4444" if _tisv >= 5 else "#F59E0B" if _tisv >= 3 else "#22C55E"
                    H(f'<div style="background:#1E293B;border-radius:8px;padding:12px;text-align:center;margin:8px 0;">'
                      f'<div style="font-size:.6rem;color:#64748B;text-transform:uppercase;">TIMI</div>'
                      f'<div style="font-size:2.2rem;font-weight:900;color:{_ticol};">{_tisv}/7</div>'
                      f'<div style="font-size:.72rem;color:#94A3B8;">{_tires.get("interpretation","")}</div>'
                      f'</div>')
                    AL(_tires.get("recommendation",""), "danger" if _tisv >= 5 else "warning" if _tisv >= 3 else "info")
                    CARD_END()

                CARD("Algoplus — Non communicant", "")
                _al1, _al2 = st.columns(2)
                _alv = _al1.checkbox("Visage",       key=WK("alg_v"))
                _alr = _al2.checkbox("Regard",       key=WK("alg_r"))
                _alp = _al1.checkbox("Plaintes",     key=WK("alg_p"))
                _ala = _al2.checkbox("Attitudes",    key=WK("alg_a"))
                _alc = _al1.checkbox("Comportement", key=WK("alg_c"))
                _alres = calculer_algoplus(_alv, _alr, _alp, _ala, _alc)
                AL(_alres.get("interpretation",""),
                   "danger" if (_alres.get("score_val") or 0) >= 2 else "success")
                AL(_alres.get("recommendation",""), "info")
                CARD_END()

        with _SC[1]:
            _s2l, _s2r = st.columns(2)
            with _s2l:
                CARD("CURB-65 — Pneumonie", "")
                _cbc = st.checkbox("Confusion",         key=WK("cb_c"))
                _cbu = st.checkbox("Urée > 7 mmol/l",  key=WK("cb_u"))
                _cbr = st.checkbox("FR ≥ 30/min",      key=WK("cb_r"), value=(SS.v_fr or 16) >= 30)
                _cbb = st.checkbox("PAS < 90",          key=WK("cb_b"), value=(SS.v_pas or 120) < 90)
                _cba = st.checkbox("Âge ≥ 65",          key=WK("cb_a"), value=age >= 65)
                _cbres = calculer_curb65(_cbc, _cbu, _cbr, _cbb, _cba)
                AL(_cbres.get("interpretation",""), "danger" if (_cbres.get("score_val") or 0) >= 3 else
                   "warning" if (_cbres.get("score_val") or 0) == 2 else "success")
                AL(_cbres.get("recommendation",""), "info")
                CARD_END()

            with _s2r:
                CARD("Wells EP", "")
                _we1, _we2 = st.columns(2)
                _wetvp = _we1.checkbox("Symptômes TVP",   key=WK("we_tvp"))
                _weep  = _we2.checkbox("EP probable",     key=WK("we_ep"))
                _wefc  = _we1.checkbox("FC > 100",        key=WK("we_fc"), value=(SS.v_fc or 80) > 100)
                _weim  = _we2.checkbox("Immobilisation",  key=WK("we_im"))
                _wean  = _we1.checkbox("ATCD TVP/EP",     key=WK("we_an"))
                _wehe  = _we2.checkbox("Hémoptysie",      key=WK("we_he"))
                _weca  = _we1.checkbox("Cancer",          key=WK("we_ca"))
                _weres = calculer_wells_ep(_wetvp, _weep, _wefc, _weim, _wean, _wehe, _weca)
                AL(_weres.get("interpretation",""), "danger" if (_weres.get("score_val") or 0) > 4 else
                   "warning" if (_weres.get("score_val") or 0) > 1 else "success")
                AL(_weres.get("recommendation",""), "info")
                CARD_END()

        with _SC[2]:
            _s3l, _s3r = st.columns(2)
            with _s3l:
                CARD("Ottawa — Cheville / Pied", "")
                _otap = st.checkbox("Incapacité d'appui (4 pas)", key=WK("ot_ap"))
                _ot1, _ot2 = st.columns(2)
                _otmm = _ot1.checkbox("Malléole médiale",  key=WK("ot_mm"))
                _ottl = _ot2.checkbox("Malléole latérale", key=WK("ot_tl"))
                _ot5m = _ot1.checkbox("Base 5e métatar.", key=WK("ot_5m"))
                _otnv = _ot2.checkbox("Naviculaire",       key=WK("ot_nv"))
                _otres = regle_ottawa_cheville(_otmm, _ottl, _ot5m, _otnv, _otap)
                AL(_otres.get("interpretation",""), "warning" if _otres.get("score_val") else "success")
                AL(_otres.get("recommendation",""), "info")
                CARD_END()
            with _s3r:
                CARD("Canadienne — TDM crânien (GCS 13-15)", "")
                _cc1, _cc2 = st.columns(2)
                _ccg  = _cc1.checkbox("GCS < 15 à 2h",        key=WK("cc_g"))
                _ccs  = _cc2.checkbox("Fracture ouverte",      key=WK("cc_s"))
                _ccf  = _cc1.checkbox("Fracture base crâne",   key=WK("cc_f"))
                _ccv  = _cc2.checkbox("Vomissements ≥ 2",     key=WK("cc_v"))
                _cca  = _cc1.checkbox("Âge ≥ 65",             key=WK("cc_a"), value=age >= 65)
                _ccam = _cc2.checkbox("Amnésie ≥ 30 min",     key=WK("cc_am"))
                _ccm  = _cc1.checkbox("Mécanisme dangereux",   key=WK("cc_m"))
                _ccres = regle_canadian_ct(_ccg, _ccs, _ccf, _ccv, _cca, _ccam, _ccm)
                AL(_ccres.get("interpretation",""), "danger" if (_ccres.get("score_val") or 0) == 2 else
                   "warning" if (_ccres.get("score_val") or 0) == 1 else "success")
                AL(_ccres.get("recommendation",""), "info")
                CARD_END()

        DISC()


    # ═══════════════════════════════════════════════════════════════════════════
    # ONGLET 4 — SUIVI (Réévaluation + Historique + SBAR)
    # ═══════════════════════════════════════════════════════════════════════════
    with T[4]:
        _ST = st.tabs(["🔄 Réévaluation", "📜 Historique", "📡 SBAR"])

        with _ST[0]:
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
                _ren2, _ = calculer_news2(_re_fr, _re_spo2, o2, _re_temp, _re_pas,
                                          _re_fc, _re_gcs, SS.v_bpco)
                _reniv, _rejust, _ = french_triage(SS.motif, SS.det, _re_fc, _re_pas, _re_spo2,
                                                    _re_fr, _re_gcs, _re_temp, age, _ren2, SS.gl)
                _delta = _ren2 - SS.v_news2
                st.metric("NEWS2 réévaluation", _ren2, delta=_delta, delta_color="inverse")
                TRI_CARD_INLINE(_reniv, _rejust, _ren2)
                if _delta > 0:   AL("NEWS2 en hausse — Réévaluation médicale urgente", "danger")
                elif _delta < 0: AL("NEWS2 en baisse — Amélioration clinique", "success")

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
                "Ceftriaxone IV", "Glucose 30% IV", "Litican® IM", "Tramadol",
                "Midazolam buccal", "Acide tranexamique IV", "Autre",
            ], key="re_5b_med")
            _dose_5b = st.text_input("Dose", key="re_5b_dose", placeholder="ex: 1 g IV en 15 min")
            _voie_5b = st.selectbox("Voie", ["IV","IM","SC","Buccale","IN","Nébulisation","PO"], key="re_5b_voie")
            CHECKLIST_5B(medicament=_med_5b, dose=_dose_5b, voie=_voie_5b,
                         poids=poids, uid=SS.uid_cur or SS.uid)
            DISC()

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
            DISC()

        with _ST[2]:
            if not SS.niv:
                AL("Calculer d'abord le triage (onglet ⚡ Triage)", "info")
            else:
                _sbar = build_sbar(age, SS.motif, SS.cat, atcd, alg, o2,
                    SS.v_temp, SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr, SS.v_gcs,
                    SS.eva, SS.v_news2, SS.niv, SS.just, SS.crit,
                    SS.op or "IAO", SS.gl)
                SBAR_RENDER(_sbar)
            DISC()

except Exception as _e:
    st.error(f"🚨 Erreur : {_e}")
    st.code(traceback.format_exc(), language="text")
