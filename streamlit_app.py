# streamlit_app.py — AKIR-IAO v19.0 — Système Expert Grade Hospitalier
# Développeur : Ismail Ibn-Daifa — Hainaut, Wallonie, Belgique
# Architecture : Modulaire — FRENCH SFMU V1.1 — BCFI — RGPD

import streamlit as st
import uuid, io, csv as csv_mod
from datetime import datetime

# ── Configuration page (DOIT être le premier appel Streamlit) ─────────────────
st.set_page_config(
    page_title="AKIR-IAO v19.0",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Imports modules métier ────────────────────────────────────────────────────
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
from clinical.pharmaco import (
    paracetamol, naproxene, ketorolac, diclofenac, tramadol, piritramide, morphine,
    naloxone, adrenaline, glucose, ceftriaxone, litican,
    salbutamol, furosemide, ondansetron, acide_tranexamique,
    methylprednisolone, crise_hypertensive, neutralisation_aod,
    sepsis_bundle_1h, ketamine_intranasale, vesiera,
    protocole_eva, protocole_epilepsie_ped,
)
from clinical.french_v12 import (
    FRENCH_MOTS_CAT, FRENCH_MOTIFS_RAPIDES,
    get_protocol, render_discriminants,
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
    SBAR_RENDER, DISC, build_sbar,
)

MOTS_CAT       = FRENCH_MOTS_CAT
MOTIFS_RAPIDES = FRENCH_MOTIFS_RAPIDES

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"<style>{load_css()}</style>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE — Source de vérité unique
# ═══════════════════════════════════════════════════════════════════════════════
_DEF = {
    "sid":    lambda: str(uuid.uuid4())[:8].upper(),
    "op":     "",
    "t_arr":  None,
    "t_cont": None,
    "v_temp": 37.0,
    "v_fc":   80,
    "v_pas":  120,
    "v_spo2": 98,
    "v_fr":   16,
    "v_gcs":  15,
    "v_news2": 0,
    "v_bpco": False,
    "motif":  "",
    "cat":    "",
    "det":    {},
    "eva":    0,
    "gl":     None,
    "niv":    "",
    "just":   "",
    "crit":   "",
    "reevs":  [],
    "t_reev": None,
    "histo":  [],
    "uid_cur": None,
}
for k, v in _DEF.items():
    if k not in st.session_state:
        st.session_state[k] = v() if callable(v) else v

SS = st.session_state


def _sync(widget_key: str, state_key: str) -> None:
    SS[state_key] = SS[widget_key]


def _mirror(widget_key: str, state_key: str) -> None:
    SS[widget_key] = SS[state_key]


# ═══════════════════════════════════════════════════════════════════════════════
# EN-TÊTE APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
H("""
<div class="app-hdr">
  <div class="app-hdr-title">AKIR-IAO v19.0 — Système Expert</div>
  <div class="app-hdr-sub">Aide au Triage Infirmier — Urgences — Hainaut, Wallonie, Belgique</div>
  <div class="app-hdr-tags">
    <span class="tag">FRENCH SFMU V1.1</span>
    <span class="tag">BCFI Belgique</span>
    <span class="tag">RGPD</span>
    <span class="tag">Dév. : Ismail Ibn-Daifa</span>
  </div>
</div>
""")

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Profil patient + Opérateur
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    SEC("Opérateur IAO")
    op_in = st.text_input("Code opérateur", value=SS.op, max_chars=10, placeholder="IAO01")
    if op_in:
        SS.op = op_in.upper()

    SEC("Chronomètre")
    ca, cb = st.columns(2)
    if ca.button("⏱ Arrivée", use_container_width=True):
        SS.t_arr = datetime.now()
        SS.histo = []
        SS.reevs = []
    if cb.button("👨‍⚕️ Contact", use_container_width=True):
        SS.t_cont = datetime.now()
    if SS.t_arr:
        el = (datetime.now() - SS.t_arr).total_seconds()
        m_, s_ = divmod(int(el), 60)
        col = "#EF4444" if el > 600 else ("#F59E0B" if el > 300 else "#22C55E")
        H(f'<div style="text-align:center;font-family:monospace;font-size:2rem;'
          f'font-weight:700;color:{col};">{m_:02d}:{s_:02d}</div>')

    SEC("Patient")
    age = st.number_input("Âge (ans)", 0, 120, 45, key="p_age")
    if age == 0:
        am  = st.number_input("Âge en mois", 0, 11, 3, key="p_am")
        age = round(am / 12.0, 4)
        AL(f"Nourrisson {am} mois — Seuils pédiatriques actifs", "info")
    poids  = st.number_input("Poids (kg)", 1, 250, 70, key="p_kg")
    taille = st.number_input("Taille (cm)", 50, 220, 170, key="p_taille")

    if taille > 0 and age >= 18:
        imc = round(poids / (taille / 100) ** 2, 1)
        if   imc < 18.5: AL(f"IMC {imc} — Insuffisance pondérale", "warning")
        elif imc < 25.0: st.caption(f"IMC {imc} — Normal")
        elif imc < 30.0: AL(f"IMC {imc} — Surpoids", "info")
        elif imc < 40.0: AL(f"IMC {imc} — Obésité", "warning")
        else:             AL(f"IMC {imc} — Obésité morbide ≥ 40 — Adapter doses opioïdes", "danger")

    # ── Antécédents structurés (cases à cocher) ──────────────────────────
    SEC("Antécédents (ATCD)")
    sb_a1, sb_a2 = st.columns(2)
    atcd_checks = {
        "HTA":                           sb_a1.checkbox("HTA", key="sb_hta"),
        "Insuffisance cardiaque":        sb_a2.checkbox("Insuff. cardiaque", key="sb_ic"),
        "Coronaropathie / SCA antérieur": sb_a1.checkbox("Coronaropathie", key="sb_coro"),
        "AVC / AIT antérieur":           sb_a2.checkbox("AVC / AIT", key="sb_avc"),
        "BPCO":                          sb_a1.checkbox("BPCO", key="sb_bpco"),
        "Asthme":                        sb_a2.checkbox("Asthme", key="sb_asthme"),
        "Diabète type 2":                sb_a1.checkbox("Diabète T2", key="sb_diab2"),
        "Diabète type 1":                sb_a2.checkbox("Diabète T1", key="sb_diab1"),
        "Insuffisance rénale chronique": sb_a1.checkbox("Insuff. rénale", key="sb_ir"),
        "Insuffisance hépatique":        sb_a2.checkbox("Insuff. hépatique", key="sb_ih"),
        "Épilepsie":                     sb_a1.checkbox("Épilepsie", key="sb_epi"),
        "Fibrillation atriale":          sb_a2.checkbox("FA", key="sb_fa"),
        "Drépanocytose":                 sb_a1.checkbox("Drépanocytose", key="sb_drep"),
        "Immunodépression":              sb_a2.checkbox("Immunodépression", key="sb_immuno"),
    }

    SEC("Facteurs favorisants")
    sb_f1, sb_f2 = st.columns(2)
    risk_checks = {
        "Grossesse":                     sb_f1.checkbox("Grossesse", key="sb_gros"),
        "Allaitement":                   sb_f2.checkbox("Allaitement", key="sb_allait"),
        "Obésité morbide (IMC ≥ 40)":   sb_f1.checkbox("Obésité IMC≥40", key="sb_ob"),
        "Chirurgie récente (<4 sem.)":   sb_f2.checkbox("Chir. récente", key="sb_chir"),
        "Tabagisme":                     sb_f1.checkbox("Tabagisme", key="sb_tabac"),
    }
    if risk_checks.get("Grossesse"):
        trimestre = st.selectbox("Trimestre", ["T1 (< 14 SA)", "T2 (14-28 SA)", "T3 (> 28 SA)"], key="sb_trim")
        AL(f"Grossesse {trimestre} — Adapter les thérapeutiques", "warning")

    SEC("Traitements en cours")
    sb_t1, sb_t2 = st.columns(2)
    trt_checks = {
        "Anticoagulants/AOD":            sb_t1.checkbox("Anticoagulants", key="sb_acg"),
        "Antiagrégants plaquettaires":   sb_t2.checkbox("Antiagrégants", key="sb_aap"),
        "Bêta-bloquants":                sb_t1.checkbox("Bêtabloquants", key="sb_beta"),
        "Corticoïdes au long cours":     sb_t2.checkbox("Corticoïdes", key="sb_cort"),
        "IMAO (inhibiteurs MAO)":        sb_t1.checkbox("IMAO", key="sb_imao"),
        "Chimiothérapie en cours":       sb_t2.checkbox("Chimio", key="sb_chimo"),
    }

    # Liste ATCD consolidée (cases + multiselect libre)
    _all_checks = {**atcd_checks, **risk_checks, **trt_checks}
    _base_atcd  = [lbl for lbl, chk in _all_checks.items() if chk]
    other_atcd  = st.multiselect(
        "Autres antécédents", [a for a in ATCD if a not in _base_atcd], key="p_atcd_other"
    )
    atcd = _base_atcd + other_atcd

    alg  = st.text_input("Allergies connues", key="p_alg", placeholder="ex: Pénicilline")
    o2   = st.checkbox("O₂ supplémentaire", key="p_o2")

    # Alertes pharmacovigilance immédiates (sidebar)
    if trt_checks.get("IMAO (inhibiteurs MAO)"):
        AL("IMAO — Tramadol CONTRE-INDIQUÉ ABSOLU", "danger")
    if atcd_checks.get("Immunodépression") or trt_checks.get("Chimiothérapie en cours"):
        AL("Immunodéprimé — Seuil fébrile abaissé à 38.3°C", "warning")
    if atcd_checks.get("Drépanocytose"):
        AL("Drépanocytose — Morphine titrée précoce si EVA ≥ 6", "warning")
    if trt_checks.get("Anticoagulants/AOD"):
        AL("Anticoagulants — Tout traumatisme = Tri 2 minimum", "warning")
    if atcd_checks.get("Insuffisance rénale chronique"):
        AL("Insuff. rénale — AINS contre-indiqués", "danger")
    if risk_checks.get("Grossesse"):
        AL("Grossesse — AINS CI au T3, morphine avec prudence", "warning")
    if trt_checks.get("Bêta-bloquants"):
        AL("Bêtabloquants — FC masquée, tachycardie relative", "warning")

    SEC("Session RGPD")
    st.caption(f"Session : {SS.sid}")
    if st.button("🔄 Nouvelle session", use_container_width=True):
        for k, v in _DEF.items():
            SS[k] = v() if callable(v) else v
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# ONGLETS PRINCIPAUX
# ═══════════════════════════════════════════════════════════════════════════════
T = st.tabs([
    "⚡ Tri Rapide",
    "📊 Vitaux & GCS",
    "🔍 Anamnèse",
    "⚖️ Triage",
    "🧮 Scores Cliniques",
    "💊 Pharmacie",
    "🔄 Réévaluation",
    "📋 Historique",
    "📡 SBAR",
])


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 0 — TRI RAPIDE
# ═══════════════════════════════════════════════════════════════════════════════
with T[0]:
    CARD("Constantes vitales", "")
    c1, c2, c3 = st.columns(3)
    _mirror("r_t",   "v_temp"); _mirror("r_fc",  "v_fc");  _mirror("r_pas", "v_pas")
    _mirror("r_sp",  "v_spo2"); _mirror("r_fr",  "v_fr")
    SS.v_temp = c1.number_input("Température (°C)", 30.0, 45.0, step=0.1, key="r_t",
                                 on_change=_sync, args=("r_t", "v_temp"))
    SS.v_fc   = c2.number_input("FC (bpm)",   20, 220, key="r_fc",
                                 on_change=_sync, args=("r_fc", "v_fc"))
    SS.v_pas  = c3.number_input("PAS (mmHg)", 40, 260, key="r_pas",
                                 on_change=_sync, args=("r_pas", "v_pas"))
    c4, c5, c6 = st.columns(3)
    SS.v_spo2 = c4.number_input("SpO2 (%)",  50, 100, key="r_sp",
                                 on_change=_sync, args=("r_sp", "v_spo2"))
    SS.v_fr   = c5.number_input("FR (/min)",  5,  60, key="r_fr",
                                 on_change=_sync, args=("r_fr", "v_fr"))
    SS.v_gcs  = c6.number_input("GCS (3-15)", 3,  15, int(SS.v_gcs), key="r_gcs")
    CARD_END()

    CARD("Motif & Sécurité", "")
    SS.v_bpco = st.checkbox("Patient BPCO connu ?", key="r_bp",
                             value=("BPCO" in atcd))
    if SS.v_bpco:
        BPCO_WIDGET(True)

    SS.v_news2, nw = calculer_news2(SS.v_fr, SS.v_spo2, o2, SS.v_temp,
                                     SS.v_pas, SS.v_fc, SS.v_gcs, SS.v_bpco)
    for w in nw:
        AL(w, "danger" if "IMMÉDIAT" in w or "ENGAGEMENT" in w else "warning")
    GAUGE(SS.v_news2, SS.v_bpco)

    SS.motif = st.selectbox("Motif de recours", MOTIFS_RAPIDES, key="r_mot")
    SS.cat   = "Tri rapide"
    SS.eva   = int(st.select_slider("EVA", [str(i) for i in range(11)], "0", key="r_eva"))
    det = {"eva": SS.eva, "atcd": atcd}

    det["purpura"] = st.checkbox("Purpura non effaçable (test du verre)", key="r_pur")
    if det.get("purpura"):
        PURPURA(det)

    gl_r = GLYC_WIDGET("r_gl", "Glycémie capillaire (mg/dl)")
    if gl_r:
        det["glycemie_mgdl"] = gl_r
        SS.gl = gl_r

    N2_BANNER(SS.v_news2)
    CARD_END()

    if st.button("⚡ Calculer le triage", type="primary", use_container_width=True):
        SS.niv, SS.just, SS.crit = french_triage(
            SS.motif, det, SS.v_fc, SS.v_pas, SS.v_spo2,
            SS.v_fr, SS.v_gcs, SS.v_temp, age, SS.v_news2, SS.gl,
        )
        SS.det = det
        TRI_CARD_INLINE(SS.niv, SS.just, SS.v_news2)
        D, A = verifier_coherence(SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr,
                                   SS.v_gcs, SS.v_temp, SS.eva, SS.motif,
                                   atcd, det, SS.v_news2, SS.gl)
        for d in D: AL(d, "danger")
        for a in A: AL(a, "warning")

    VITAUX(SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr, SS.v_temp, SS.v_gcs, SS.v_bpco)
    DISC()


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 1 — VITAUX & GCS
# ═══════════════════════════════════════════════════════════════════════════════
with T[1]:
    CARD("Paramètres vitaux détaillés", "")
    v1, v2, v3 = st.columns(3)
    SS.v_temp  = v1.number_input("Température (°C)", 30.0, 45.0, float(SS.v_temp), 0.1, key="v_t2")
    SS.v_fc    = v2.number_input("FC (bpm)",   20, 220, int(SS.v_fc),   key="v_fc2")
    SS.v_pas   = v3.number_input("PAS (mmHg)", 40, 260, int(SS.v_pas),  key="v_pas2")
    v4, v5, v6 = st.columns(3)
    SS.v_spo2  = v4.number_input("SpO2 (%)",   50, 100, int(SS.v_spo2), key="v_sp2")
    SS.v_fr    = v5.number_input("FR (/min)",   5,  60, int(SS.v_fr),   key="v_fr2")
    SS.v_gcs   = v6.number_input("GCS (3-15)", 3,  15, int(SS.v_gcs),   key="v_gcs2")
    SS.v_bpco  = st.checkbox("Patient BPCO", key="v_bp2", value=SS.v_bpco or ("BPCO" in atcd))
    CARD_END()

    CARD("GCS Détaillé", "")
    gcs_y = st.select_slider("Ouverture des yeux",
                              [1, 2, 3, 4], 4, key="gcs_y",
                              format_func=lambda x: {1:"1–Absente",2:"2–Douleur",3:"3–Bruit",4:"4–Spontanée"}[x])
    gcs_v = st.select_slider("Réponse verbale",
                              [1, 2, 3, 4, 5], 5, key="gcs_v",
                              format_func=lambda x: {1:"1–Aucune",2:"2–Sons",3:"3–Mots",4:"4–Confus",5:"5–Orientée"}[x])
    gcs_m = st.select_slider("Réponse motrice",
                              [1, 2, 3, 4, 5, 6], 6, key="gcs_m",
                              format_func=lambda x: {1:"1–Aucune",2:"2–Extension",3:"3–Flexion anorm.",
                                                      4:"4–Retrait",5:"5–Localise",6:"6–Obéit"}[x])
    gcs_res = calculer_gcs(gcs_y, gcs_v, gcs_m, age)
    SS.v_gcs = gcs_res["score_val"] or 15
    AL(gcs_res["interpretation"], "danger" if (gcs_res["score_val"] or 15) <= 8 else
       "warning" if (gcs_res["score_val"] or 15) <= 12 else "success")
    AL(gcs_res["recommendation"], "info")
    CARD_END()

    SS.v_news2, nw = calculer_news2(SS.v_fr, SS.v_spo2, o2, SS.v_temp,
                                     SS.v_pas, SS.v_fc, SS.v_gcs, SS.v_bpco)
    for w in nw:
        AL(w, "danger" if "IMMÉDIAT" in w or "ENGAGEMENT" in w else "warning")
    N2_BANNER(SS.v_news2)
    GAUGE(SS.v_news2, SS.v_bpco)
    VITAUX(SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr, SS.v_temp, SS.v_gcs, SS.v_bpco)

    sh_val = si(SS.v_fc, SS.v_pas)
    AL(f"Shock Index {sh_val}" + (" — CHOC PROBABLE" if sh_val >= 1 else " — Normal"),
       "danger" if sh_val >= 1 else ("warning" if sh_val >= 0.8 else "success"))

    if age < 18:
        sv, stxt, salerte = sipa(SS.v_fc, age)
        AL(stxt, "danger" if salerte else "success")
    DISC()


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 2 — ANAMNÈSE
# ═══════════════════════════════════════════════════════════════════════════════
with T[2]:
    non_comm = ("Démence" in atcd or (age >= 75 and SS.v_gcs < 15))
    eva_result = EVA_WIDGET_COMPLET(key_prefix="ana", age=age, non_communicant=non_comm)
    SS.eva = eva_result.get("eva", 0)
    SS.det.update({"eva": SS.eva, "pqrst": eva_result.get("pqrst", {}), "atcd": atcd})

    CARD("Motif de recours", "")
    SS.cat   = st.selectbox("Catégorie", list(MOTS_CAT.keys()), key="a_cat")
    SS.motif = st.selectbox("Motif principal", MOTS_CAT[SS.cat], key="a_mot")
    CARD_END()

    if "Brûlure" in SS.motif or "brulure" in SS.motif.lower():
        brul = SCHEMA_BRULURES(poids=poids, age=age)
        SS.det.update({"surface_pct": brul["surface_pct"], "baux": brul["baux"],
                        "profondeur": brul["profondeur"]})

    det = SS.det.copy()
    det["atcd"] = atcd
    det = QUESTIONS_AVANCEES(
        motif=SS.motif, details=det, age=age,
        atcd=atcd, poids=poids, gl_global=SS.gl,
    )
    if det.get("glycemie_mgdl") and not SS.gl:
        SS.gl = det["glycemie_mgdl"]
    if det.get("purpura") or det.get("neff"):
        PURPURA(det)
    SS.det = det

    if SS.motif:
        pa_result = PRESCRIPTIONS_ANTICIPEES(
            motif=SS.motif, niv=SS.niv or "3B",
            poids=poids, age=age, atcd=atcd,
            eva=SS.eva, spo2=SS.v_spo2, pas=SS.v_pas,
        )
        if pa_result:
            SS.det["pa_tracabilite"] = pa_result
    DISC()


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 3 — TRIAGE
# ═══════════════════════════════════════════════════════════════════════════════
with T[3]:
    if not SS.motif:
        SS.motif = "Fièvre"; SS.cat = "Infectieux"

    SS.v_news2, nw = calculer_news2(SS.v_fr, SS.v_spo2, o2, SS.v_temp,
                                     SS.v_pas, SS.v_fc, SS.v_gcs, SS.v_bpco)
    for w in nw:
        AL(w, "danger" if "IMMÉDIAT" in w or "ENGAGEMENT" in w else "warning")

    det = SS.det or {}
    if not det.get("glycemie_mgdl") and not SS.gl:
        gl_t = GLYC_WIDGET("t_gl", "Glycémie capillaire (mg/dl)")
        if gl_t:
            det["glycemie_mgdl"] = gl_t
            SS.gl = gl_t
            SS.det = det
    gl_t = det.get("glycemie_mgdl") or SS.gl

    SS.niv, SS.just, SS.crit = french_triage(
        SS.motif, det, SS.v_fc, SS.v_pas, SS.v_spo2,
        SS.v_fr, SS.v_gcs, SS.v_temp, age, SS.v_news2, gl_t,
    )
    N2_BANNER(SS.v_news2)
    PURPURA(det)
    GAUGE(SS.v_news2, SS.v_bpco)
    TRI_CARD_INLINE(SS.niv, SS.just, SS.v_news2)
    st.caption(f"Critère FRENCH : {SS.crit}")

    D, A = verifier_coherence(SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr,
                               SS.v_gcs, SS.v_temp, SS.eva, SS.motif,
                               atcd, det, SS.v_news2, gl_t)
    for d in D: AL(d, "danger")
    for a in A: AL(a, "warning")

    # Discriminants FRENCH
    proto = get_protocol(SS.motif)
    if proto and proto.get("criteria"):
        CARD("Critères discriminants FRENCH", "")
        render_discriminants(SS.motif, key="t_disc")
        CARD_END()

    if st.button("💾 Enregistrer ce patient", type="primary", use_container_width=True):
        uid = enregistrer_patient({
            "motif": SS.motif, "cat": SS.cat, "niv": SS.niv, "n2": SS.v_news2,
            "fc": SS.v_fc, "pas": SS.v_pas, "spo2": SS.v_spo2,
            "fr": SS.v_fr, "temp": SS.v_temp, "gcs": SS.v_gcs, "op": SS.op,
        })
        SS.uid_cur = uid
        SS.reevs   = []
        SS.t_reev  = datetime.now()
        SS.histo.insert(0, {
            "uid": uid, "h": datetime.now().strftime("%H:%M"),
            "motif": SS.motif, "niv": SS.niv, "n2": SS.v_news2,
        })
        st.success(f"✅ Patient enregistré — UID : {uid}")

    # ── Synthèse IAO — Copy-pasteable pour le dossier médical ─────────────
    if SS.niv:
        st.divider()
        CARD("📋 Synthèse IAO — Copier pour le dossier", "")
        _si_val = round((SS.v_fc or 80) / max(1, (SS.v_pas or 120)), 2)
        _gl_txt = f"{SS.gl:.0f} mg/dl ({SS.gl/18.016:.1f} mmol/l)" if SS.gl else "Non mesurée"
        _atcd_txt = ", ".join(atcd) if atcd else "Aucun antécédent connu"
        _alg_txt  = alg if alg else "Aucune allergie connue"
        _now_txt  = datetime.now().strftime("%d/%m/%Y à %H:%M")

        _synthese_txt = f"""SYNTHÈSE IAO — {_now_txt}
Opérateur : {SS.op or "IAO"} | Session RGPD : {SS.uid_cur or "—"}
{"═" * 55}
NIVEAU DE TRIAGE : {SS.niv} — {LABELS.get(SS.niv, "")}
Justification    : {SS.just}
Référence FRENCH : {SS.crit}
Orientation      : {SECTEURS.get(SS.niv, "—")} | Délai médecin ≤ {DELAIS.get(SS.niv, "?")} min
{"─" * 55}
MOTIF DE RECOURS : {SS.motif} ({SS.cat})
EVA / Douleur    : {SS.eva}/10
{"─" * 55}
CONSTANTES VITALES
  Température    : {SS.v_temp}°C
  FC             : {SS.v_fc} bpm
  PAS            : {SS.v_pas} mmHg
  SpO2           : {SS.v_spo2} %
  FR             : {SS.v_fr} /min
  GCS            : {SS.v_gcs}/15
  Shock Index    : {_si_val}
  NEWS2          : {SS.v_news2}
  Glycémie       : {_gl_txt}
{"─" * 55}
ANTÉCÉDENTS      : {_atcd_txt}
ALLERGIES        : {_alg_txt}
O2 supplémentaire: {"OUI" if o2 else "Non"}
{"═" * 55}
Réf. FRENCH Triage SFMU V1.1 | BCFI Belgique
Urgences — Province de Hainaut, Wallonie, Belgique
Dév. exclusif : Ismail Ibn-Daifa — AKIR-IAO v19.0"""

        st.code(_synthese_txt, language=None)
        st.download_button(
            "📥 Télécharger la synthèse (.txt)",
            data=_synthese_txt,
            file_name=f"SyntheseIAO_{datetime.now().strftime('%Y%m%d_%H%M')}_Tri{SS.niv}.txt",
            mime="text/plain",
            use_container_width=True,
        )
        CARD_END()

    DISC()


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 4 — SCORES CLINIQUES
# ═══════════════════════════════════════════════════════════════════════════════
with T[4]:
    S = st.tabs(["Cardio / Neuro", "Infectio / Respiratoire", "Règles Imagerie"])

    # ── S[0] CARDIO / NEURO ────────────────────────────────────────────────
    with S[0]:
        s_l, s_r = st.columns(2)

        with s_l:
            CARD("qSOFA — Dépistage Sepsis", "")
            st.caption("Seymour CW et al., JAMA 2016")
            qs = calculer_qsofa(SS.v_fr or 16, SS.v_gcs or 15, SS.v_pas or 120)
            sv = qs["score_val"] or 0
            AL(qs["interpretation"], "danger" if sv >= 2 else "warning" if sv == 1 else "success")
            AL(qs["recommendation"], "info")
            CARD_END()

            CARD("Score HEART — Douleur thoracique", "")
            st.caption("Six AJ et al., NHJ 2008")
            h1, h2 = st.columns(2)
            h_hist = h1.select_slider("Histoire", [0, 1, 2], key="ht_h",
                format_func=lambda x: {0:"0–Peu évocateur",1:"1–Modérément",2:"2–Très suspect"}[x])
            h_ecg  = h2.select_slider("ECG",     [0, 1, 2], key="ht_e",
                format_func=lambda x: {0:"0–Normal",1:"1–Non spéc.",2:"2–Bloc/STEMI"}[x])
            h_age  = h1.select_slider("Âge",     [0, 1, 2], key="ht_a",
                format_func=lambda x: {0:"0–<45 ans",1:"1–45-65",2:"2–>65 ans"}[x])
            h_rfcv = h2.select_slider("FRCV",    [0, 1, 2], key="ht_r",
                format_func=lambda x: {0:"0–Aucun",1:"1–1-2",2:"2–≥3 ou ATCD"}[x])
            h_trop = h1.select_slider("Troponine",[0, 1, 2], key="ht_t",
                format_func=lambda x: {0:"0–Normale",1:"1–1-3x N",2:"2–>3x N"}[x])
            ht = calculer_heart(h_hist, h_ecg, h_age, h_rfcv, h_trop)
            AL(ht["interpretation"], "danger" if (ht["score_val"] or 0) >= 7 else
               "warning" if (ht["score_val"] or 0) >= 4 else "success")
            AL(ht["recommendation"], "info")
            CARD_END()

            # TIMI contextuel — affiché UNIQUEMENT si motif = douleur thoracique
            _motif_norm_scores = (SS.motif or "").lower()
            _is_thoracique = any(k in _motif_norm_scores for k in ("thoracique", "sca", "coronaire", "infarctus"))
            if _is_thoracique:
                CARD("Score TIMI — UA/NSTEMI (contexte SCA)", "")
                st.caption("Antman EM et al., JAMA 2000 — Affiché car motif : douleur thoracique")
                st.info("ℹ️ TIMI activé automatiquement car le motif sélectionné est une douleur thoracique")
                ti1, ti2 = st.columns(2)
                ti_age   = ti1.checkbox("Âge ≥ 65 ans", key="ti_age", value=age >= 65)
                ti_frcv  = ti2.checkbox("≥ 3 facteurs de risque CV", key="ti_frcv")
                ti_sten  = ti1.checkbox("Sténose coronaire ≥ 50 % connue", key="ti_sten")
                ti_ecg   = ti2.checkbox("Déviation ST à l'ECG", key="ti_ecg")
                ti_ang   = ti1.checkbox("≥ 2 épisodes angineux / 24 h", key="ti_ang")
                ti_asp   = ti2.checkbox("Aspirine dans les 7 jours", key="ti_asp")
                ti_trop  = ti1.checkbox("Marqueurs cardiaques positifs", key="ti_trop")
                ti_res = calculer_timi(ti_age, ti_frcv, ti_sten, ti_ecg, ti_ang, ti_asp, ti_trop)
                ti_score = ti_res.get("score_val") or 0
                H(f"""<div style="background:#1E293B;border-radius:10px;padding:14px;margin:10px 0;text-align:center;">
                  <div style="font-size:.65rem;color:#64748B;text-transform:uppercase;letter-spacing:.1em;">Score TIMI</div>
                  <div style="font-size:2.5rem;font-weight:900;color:{'#EF4444' if ti_score>=5 else '#F59E0B' if ti_score>=3 else '#22C55E'};">{ti_score}/7</div>
                  <div style="font-size:.75rem;color:#94A3B8;margin-top:4px;">{ti_res.get("interpretation","")}</div>
                </div>""")
                AL(ti_res.get("recommendation",""), "danger" if ti_score >= 5 else "warning" if ti_score >= 3 else "info")
                CARD_END()
            else:
                H('<div style="background:#F1F5F9;border-radius:10px;padding:12px;text-align:center;color:#94A3B8;font-size:.75rem;margin:8px 0;">TIMI NSTEMI — Disponible uniquement si motif = Douleur thoracique / SCA</div>')

        with s_r:
            CARD("BE-FAST — Dépistage AVC", "")
            st.caption("Kothari RU, Ann Emerg Med 1999")
            f1, f2 = st.columns(2)
            bf_ba  = f1.checkbox("Balance (équilibre)", key="bf_b")
            bf_ey  = f2.checkbox("Eyes (vision)", key="bf_e")
            bf_fa  = f1.checkbox("Face (asymétrie)", key="bf_f")
            bf_ar  = f2.checkbox("Arm (déficit moteur)", key="bf_a")
            bf_sp  = f1.checkbox("Speech (langage)", key="bf_sp")
            bf_ti  = f2.text_input("Heure dernière fois vu bien", key="bf_t", placeholder="14:30")
            bf_res = evaluer_fast(bf_fa, bf_ar, bf_sp, bf_ti, bf_ba, bf_ey)
            AL(bf_res["interpretation"], "danger" if (bf_res["score_val"] or 0) >= 1 else "success")
            AL(bf_res["recommendation"], "info")
            CARD_END()

            CARD("Algoplus — Douleur non communicant", "")
            st.caption("Rat P et al., Eur J Pain 2011")
            a1, a2 = st.columns(2)
            alg_v = a1.checkbox("Visage douloureux", key="alg_v")
            alg_r = a2.checkbox("Regard distant", key="alg_r")
            alg_p = a1.checkbox("Plaintes verbales", key="alg_p")
            alg_a = a2.checkbox("Attitudes défensives", key="alg_a")
            alg_c = a1.checkbox("Comportement inhabituels", key="alg_c")
            alg_res = calculer_algoplus(alg_v, alg_r, alg_p, alg_a, alg_c)
            AL(alg_res["interpretation"], "danger" if (alg_res["score_val"] or 0) >= 2 else "success")
            AL(alg_res["recommendation"], "info")
            CARD_END()

    # ── S[1] INFECTIO / RESPIRATOIRE ─────────────────────────────────────
    with S[1]:
        s2_l, s2_r = st.columns(2)

        with s2_l:
            CARD("CURB-65 — Pneumonie communautaire", "")
            st.caption("Lim WS et al., Thorax 2003")
            cb_c = st.checkbox("Confusion", key="cb_c")
            cb_u = st.checkbox("Urée > 7 mmol/l", key="cb_u")
            cb_r = st.checkbox("FR ≥ 30/min", key="cb_r",
                                value=(SS.v_fr or 16) >= 30)
            cb_b = st.checkbox("PAS < 90 ou PAD < 60 mmHg", key="cb_b",
                                value=(SS.v_pas or 120) < 90)
            cb_a = st.checkbox("Âge ≥ 65 ans", key="cb_a", value=age >= 65)
            cb_res = calculer_curb65(cb_c, cb_u, cb_r, cb_b, cb_a)
            AL(cb_res["interpretation"], "danger" if (cb_res["score_val"] or 0) >= 3 else
               "warning" if (cb_res["score_val"] or 0) == 2 else "success")
            AL(cb_res["recommendation"], "info")
            CARD_END()

            CARD("Wells TVP", "")
            st.caption("Wells PS et al., Lancet 1997")
            wt1, wt2 = st.columns(2)
            wt_ca = wt1.checkbox("Cancer actif", key="wt_ca")
            wt_im = wt2.checkbox("Immobilisation > 3 j", key="wt_im")
            wt_ch = wt1.checkbox("Chirurgie récente", key="wt_ch")
            wt_se = wt2.checkbox("Sensibilité veine", key="wt_se")
            wt_oe = wt1.checkbox("Œdème à godet", key="wt_oe")
            wt_am = wt2.checkbox("Asymétrie mollet", key="wt_am")
            wt_av = wt1.checkbox("Asymétrie membre", key="wt_av")
            wt_vc = wt2.checkbox("Veines collatérales", key="wt_vc")
            wt_an = wt1.checkbox("ATCD TVP", key="wt_an")
            wt_da = wt2.checkbox("Diag. alternatif probable", key="wt_da")
            wt_res = calculer_wells_tvp(wt_ca, wt_im, wt_ch, wt_se, wt_oe, wt_am, wt_av, wt_vc, wt_an, wt_da)
            AL(wt_res["interpretation"], "danger" if (wt_res["score_val"] or 0) >= 3 else
               "warning" if (wt_res["score_val"] or 0) >= 1 else "success")
            AL(wt_res["recommendation"], "info")
            CARD_END()

        with s2_r:
            CARD("Wells EP", "")
            st.caption("Wells PS et al., Thromb Haemost 2000")
            we1, we2 = st.columns(2)
            we_tvp = we1.checkbox("Symptômes TVP", key="we_tvp")
            we_ep  = we2.checkbox("EP plus probable", key="we_ep")
            we_fc  = we1.checkbox("FC > 100/min", key="we_fc", value=(SS.v_fc or 80) > 100)
            we_im  = we2.checkbox("Immobilisation/chirurgie", key="we_im")
            we_an  = we1.checkbox("ATCD TVP/EP", key="we_an")
            we_he  = we2.checkbox("Hémoptysie", key="we_he")
            we_ca  = we1.checkbox("Cancer", key="we_ca")
            we_res = calculer_wells_ep(we_tvp, we_ep, we_fc, we_im, we_an, we_he, we_ca)
            AL(we_res["interpretation"], "danger" if (we_res["score_val"] or 0) > 4 else
               "warning" if (we_res["score_val"] or 0) > 1 else "success")
            AL(we_res["recommendation"], "info")
            CARD_END()

            CARD("CFS — Clinical Frailty Scale", "")
            st.caption("Rockwood K et al., CMAJ 2005")
            cfs_n = st.select_slider("Niveau fragilité", list(range(1, 10)), 1, key="cfs_n",
                format_func=lambda x: {1:"1–Très robuste",2:"2–Bien portant",3:"3–Maladies traitées",
                    4:"4–Vulnérable",5:"5–Légèrement fragile",6:"6–Modérément fragile",
                    7:"7–Sévèrement fragile",8:"8–Très sévèrement",9:"9–Phase terminale"}[x])
            cfs_res = evaluer_cfs(cfs_n)
            AL(cfs_res["interpretation"], "danger" if cfs_n >= 7 else "warning" if cfs_n >= 5 else "success")
            AL(cfs_res["recommendation"], "info")
            CARD_END()

    # ── S[2] RÈGLES IMAGERIE ──────────────────────────────────────────────
    with S[2]:
        s3_l, s3_r = st.columns(2)

        with s3_l:
            CARD("Règles d'Ottawa — Cheville / Pied", "")
            st.caption("Stiell IG et al., JAMA 1993")
            ot_ap = st.checkbox("Incapacité d'appui (4 pas)", key="ot_ap")
            ot1, ot2 = st.columns(2)
            ot_mm = ot1.checkbox("Douleur malléole médiale", key="ot_mm")
            ot_tl = ot2.checkbox("Douleur malléole latérale", key="ot_tl")
            ot_5m = ot1.checkbox("Douleur base 5e métatarse", key="ot_5m")
            ot_nv = ot2.checkbox("Douleur naviculaire", key="ot_nv")
            ot_res = regle_ottawa_cheville(ot_mm, ot_tl, ot_5m, ot_nv, ot_ap)
            AL(ot_res["interpretation"], "warning" if (ot_res["score_val"] or 0) else "success")
            AL(ot_res["recommendation"], "info")
            CARD_END()

        with s3_r:
            CARD("Règle Canadienne — TDM cérébral (GCS 13-15)", "")
            st.caption("Stiell IG et al., Lancet 2001")
            AL("Non applicable si : GCS < 13 | coagulopathie | convulsion | < 16 ans", "warning")
            cc1, cc2 = st.columns(2)
            cc_g  = cc1.checkbox("GCS < 15 à 2 h", key="cc_g")
            cc_s  = cc2.checkbox("Suspicion fracture ouverte", key="cc_s")
            cc_f  = cc1.checkbox("Signe fracture base crâne", key="cc_f")
            cc_v  = cc2.checkbox("Vomissements ≥ 2", key="cc_v")
            cc_a  = cc1.checkbox("Âge ≥ 65 ans", key="cc_a", value=age >= 65)
            cc_am = cc2.checkbox("Amnésie ≥ 30 min", key="cc_am")
            cc_m  = cc1.checkbox("Mécanisme dangereux", key="cc_m")
            cc_res = regle_canadian_ct(cc_g, cc_s, cc_f, cc_v, cc_a, cc_am, cc_m)
            AL(cc_res["interpretation"], "danger" if (cc_res["score_val"] or 0) == 2 else
               "warning" if (cc_res["score_val"] or 0) == 1 else "success")
            AL(cc_res["recommendation"], "info")
            CARD_END()
    DISC()


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 5 — PHARMACIE
# ═══════════════════════════════════════════════════════════════════════════════
with T[5]:
    gl_ph = (SS.det.get("glycemie_mgdl") if SS.det else None) or SS.gl

    H(f"""<div style="background:linear-gradient(135deg,#004A99,#0066CC);
        color:#fff;border-radius:10px;padding:12px 18px;margin-bottom:12px;
        display:flex;justify-content:space-between;align-items:center;">
      <div>
        <div style="font-size:.7rem;opacity:.8;">Doses calculées pour</div>
        <div style="font-size:1.4rem;font-weight:800;">{poids} kg — {age} ans</div>
      </div>
      <div style="font-size:.72rem;opacity:.8;text-align:right;">
        ATCD : {len(atcd)} | Allergies : {alg or 'aucune'}
      </div>
    </div>""")

    if "IMAO (inhibiteurs MAO)" in atcd:
        AL("IMAO — TRAMADOL CONTRE-INDIQUÉ ABSOLU", "danger")
    if "Insuffisance cardiaque" in atcd:
        AL("Insuffisance cardiaque — Remplissage réduit à 15 ml/kg", "warning")
    if gl_ph is None:
        AL("Glycémie non saisie — Glucose 30 % désactivé", "warning")

    # ── Antalgiques palier 1 ──────────────────────────────────────────────
    CARD("Paracétamol IV — Palier 1", "")
    para_rx, para_err = paracetamol(poids, age, atcd)
    if para_err: AL(para_err, "danger")
    else:
        for m_, c_ in para_rx.get("alerts", []): AL(m_, c_)
        RX("Paracétamol IV (Perfalgan)", f"{para_rx['dose_g']} g",
           [para_rx["admin"], para_rx["note"]], para_rx["ref"], "1", para_rx.get("alerts", []))
    CARD_END()

    ph_c1, ph_c2 = st.columns(2)

    with ph_c1:
        CARD("Naproxène PO — AINS palier 1", "")
        nap_rx, nap_err = naproxene(poids, age, atcd)
        if nap_err: AL(nap_err, "warning")
        else: RX("Naproxène PO", f"{nap_rx['dose_mg']:.0f} mg", [nap_rx["admin"], nap_rx["note"]], nap_rx["ref"], "1")
        CARD_END()

        CARD("Taradyl® (Kétorolac) IM — AINS puissant", "")
        kt2_rx, kt2_err = ketorolac(poids, age, atcd)
        if kt2_err: AL(f"🔒 {kt2_err}", "danger")
        else:
            for m_, c_ in (kt2_rx or {}).get("alerts", []): AL(m_, c_)
            RX("Taradyl® 30 mg/ml IM", f"{(kt2_rx or {}).get('dose_mg', 30):.0f} mg",
               [(kt2_rx or {}).get("admin",""), (kt2_rx or {}).get("note","")],
               (kt2_rx or {}).get("ref","BCFI"), "1", (kt2_rx or {}).get("alerts",[]))
        CARD_END()

        CARD("Voltarène® (Diclofénac) 75 mg IM — Adulte", "")
        dic_rx, dic_err = diclofenac(poids, age, atcd)
        if dic_err: AL(f"🔒 {dic_err}", "danger")
        else:
            for m_, c_ in (dic_rx or {}).get("alerts", []): AL(m_, c_)
            RX("Voltarène® 75 mg/3 ml IM", f"{(dic_rx or {}).get('dose_mg', 75):.0f} mg",
               [(dic_rx or {}).get("admin",""), (dic_rx or {}).get("note","")],
               (dic_rx or {}).get("ref","BCFI"), "1", (dic_rx or {}).get("alerts",[]))
        CARD_END()

    with ph_c2:
        CARD("Tramadol — Palier 2", "")
        tram_rx, tram_err = tramadol(poids, age, atcd)
        if tram_err: AL(tram_err, "danger" if "contre" in tram_err.lower() else "warning")
        else:
            for m_, c_ in tram_rx.get("alerts", []): AL(m_, c_)
            RX("Tramadol (Tradonal)", f"{tram_rx['dose_mg']:.0f} mg", [tram_rx["admin"], tram_rx["note"]], tram_rx["ref"], "2")
        CARD_END()

    CARD("Piritramide IV — Palier 3 (Dipidolor)", "")
    dip_rx, dip_err = piritramide(poids, age, atcd)
    if dip_err: AL(dip_err, "danger")
    else:
        for m_, c_ in dip_rx.get("alerts", []): AL(m_, c_)
        RX("Piritramide IV (Dipidolor)", f"{dip_rx['dose_min']:.1f}–{dip_rx['dose_max']:.1f} mg",
           [dip_rx["admin"], dip_rx["note"]], dip_rx["ref"], "3", dip_rx.get("alerts", []))
    CARD_END()

    CARD("Morphine IV titrée — Palier 3", "")
    morph_rx, morph_err = morphine(poids, age, atcd)
    if morph_err: AL(morph_err, "danger")
    else:
        for m_, c_ in morph_rx.get("alerts", []): AL(m_, c_)
        RX("Morphine IV", f"{morph_rx['dose_min']:.1f}–{morph_rx['dose_max']:.1f} mg",
           [morph_rx["admin"], morph_rx["note"]], morph_rx["ref"], "3", morph_rx.get("alerts", []))
    CARD_END()

    # ── Urgences vitales ─────────────────────────────────────────────────
    ph2_c1, ph2_c2 = st.columns(2)
    with ph2_c1:
        CARD("Adrénaline IM — Anaphylaxie", "")
        ar, ae = adrenaline(poids, atcd)
        if ae: AL(ae, "danger")
        else:
            for m_, c_ in ar.get("alerts", []): AL(m_, c_)
            RX("Adrénaline IM (Sterop 1 mg/ml)", f"{ar['dose_mg']} mg",
               [ar["voie"], ar["note"], ar["rep"]], ar["ref"], "U", ar.get("alerts", []))
        CARD_END()

    with ph2_c2:
        CARD("Naloxone IV — Antidote opioïdes", "")
        dep_ph = st.checkbox("Patient dépendant aux opioïdes", key="ph_dep")
        nr, _ = naloxone(poids, age, dep_ph, atcd)
        if nr:
            for m_, c_ in nr.get("alerts", []): AL(m_, c_)
            RX("Naloxone IV (Narcan)", f"{nr['dose']} mg",
               [nr["admin"], nr["note"]], nr["ref"], "U", nr.get("alerts", []))
        CARD_END()

    CARD("Glucose 30 % IV — Hypoglycémie", "")
    if gl_ph is None:
        RX_LOCK("Glycémie capillaire non saisie — Mesurer d'abord la glycémie")
    else:
        gr, ge = glucose(poids, gl_ph, atcd)
        if ge: AL(ge, "info")
        else:
            for m_, c_ in gr.get("alerts", []): AL(m_, c_)
            RX("Glucose 30 % IV", f"{gr['dose_g']} g",
               [gr["vol"], gr["ctrl"]], gr["ref"], "U", gr.get("alerts", []))
    CARD_END()

    CARD("Ceftriaxone IV — Urgence infectieuse", "")
    cr2, ce2 = ceftriaxone(poids, age, atcd)
    if ce2: AL(ce2, "danger")
    else:
        for m_, c_ in cr2.get("alerts", []): AL(m_, c_)
        RX("Ceftriaxone IV", f"{cr2['dose_g']} g",
           [cr2["admin"], cr2["note"]], cr2["ref"], "U", cr2.get("alerts", []))
    CARD_END()

    CARD("Litican IM — Antispasmodique (Protocole Hainaut)", "")
    lr, le = litican(poids, age, atcd)
    if le: AL(le, "danger")
    else:
        for m_, c_ in lr.get("alerts", []): AL(m_, c_)
        RX("Litican IM (Tiémonium)", f"{lr['dose_mg']:.0f} mg",
           [lr["voie"], lr["dose_note"], lr["freq"]], lr["ref"], "2", lr.get("alerts", []))
    CARD_END()

    CARD("Salbutamol nébulisation — Bronchospasme", "")
    grav = st.select_slider("Gravité", ["legere", "moderee", "severe"], "moderee", key="ph_grav",
        format_func=lambda x: {"legere": "Légère", "moderee": "Modérée", "severe": "Sévère"}[x])
    sr, se = salbutamol(poids, age, grav, atcd)
    if se: AL(se, "warning")
    else: RX("Salbutamol (Ventolin) nébulisation", f"{sr['dose_mg']} mg",
             [sr["admin"], sr["dilution"], sr["debit_o2"], sr["rep"]], sr["ref"], "2")
    CARD_END()

    CARD("Sepsis Bundle — Première heure (SSC 2021)", "")
    sb_lact = st.number_input("Lactate (mmol/l — 0 si non dosé)", 0.0, 20.0, 0.0, 0.1, key="sb_l")
    sb = sepsis_bundle_1h(SS.v_pas or 120, sb_lact if sb_lact > 0 else None,
                           SS.v_temp or 37, SS.v_fc or 80, poids, atcd)
    if (sb or {}).get("choc_septique"): AL("CHOC SEPTIQUE — Réanimation immédiate", "danger")
    for m_, c_ in (sb or {}).get("alerts", []): AL(m_, c_)
    for lbl, detail, css in (sb or {}).get("checklist", []):
        H(f'<div class="al {css}" style="padding:7px 14px;margin:3px 0;font-size:.78rem;">'
          f'<input type="checkbox" style="margin-right:8px;">'
          f'<strong>{lbl}</strong> — {detail}</div>')
    CARD_END()

    CARD("Crise hypertensive — Cible adaptée à l'étiologie", "")
    AL("Cibles DIFFÉRENTES selon l'étiologie — Ne jamais baisser trop vite", "warning")
    motif_hta = st.selectbox("Contexte clinique", [
        "Urgence hypertensive standard", "AVC ischémique (non thrombolysé)",
        "AVC ischémique (si thrombolyse)", "AVC hémorragique",
        "Dissection aortique", "OAP hypertensif",
    ], key="ph_hta")
    _ch_payload, _ch_err = crise_hypertensive(SS.v_pas or 120, motif_hta, poids, atcd)
    if _ch_err:
        AL(_ch_err, "danger")
    else:
        AL(f"Objectif : {(_ch_payload or {}).get('cible', 'Cible clinique à confirmer')}", "warning")
        for m_, c_ in (_ch_payload or {}).get("alerts", []): AL(m_, c_)
    CARD_END()

    # ── Épilepsie pédiatrique ─────────────────────────────────────────────
    if age < 18:
        CARD("Protocole anticonvulsivant pédiatrique", "")
        st.caption("BCFI / Lignes directrices belges — EME Pédiatrique")
        dur_epi = float(SS.det.get("duree_min", 0) or 0) if SS.det else 0.0
        encours  = bool(SS.det.get("en_cours", False)) if SS.det else False
        eme = protocole_epilepsie_ped(poids, age, dur_epi, encours, atcd)
        _eme = eme or {}
        if _eme.get("eme_etabli"):
            AL(f"EME établi ({dur_epi:.0f} min) — Traitement 2e ligne requis", "danger")
        e1, e2 = st.columns(2)
        with e1:
            mid = _eme.get("midazolam_buccal") or {}
            RX("Midazolam buccal", mid.get("dose","?"), [mid.get("note","")], mid.get("ref","BCFI"), "2")
            diz = _eme.get("diazepam_rectal") or {}
            RX("Diazépam rectal", diz.get("dose","?"), [diz.get("note","")], diz.get("ref","BCFI"), "2")
        with e2:
            lor = _eme.get("lorazepam_iv") or {}
            RX("Lorazépam IV", lor.get("dose","?"), [lor.get("note","")], lor.get("ref","BCFI"), "2")
            if _eme.get("eme_etabli"):
                lev = _eme.get("levetiracetam_iv") or {}
                RX("Lévétiracétam IV", lev.get("dose","?"), [lev.get("note","")], lev.get("ref","BCFI"), "3")
        CARD_END()

    DISC()


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 6 — RÉÉVALUATION
# ═══════════════════════════════════════════════════════════════════════════════
with T[6]:
    CARD("Réévaluation clinique", "")
    if not SS.uid_cur:
        AL("Enregistrer d'abord un patient dans l'onglet Triage", "info")
    else:
        st.caption(f"Patient actif : {SS.uid_cur}")
        rc1, rc2, rc3 = st.columns(3)
        re_temp = rc1.number_input("T°", 30.0, 45.0, float(SS.v_temp), 0.1, key="re_t")
        re_fc   = rc1.number_input("FC",  20, 220, int(SS.v_fc),  key="re_fc")
        re_pas  = rc2.number_input("PAS", 40, 260, int(SS.v_pas), key="re_pas")
        re_spo2 = rc2.number_input("SpO2",50, 100, int(SS.v_spo2),key="re_sp")
        re_fr   = rc3.number_input("FR",   5,  60, int(SS.v_fr),  key="re_fr")
        re_gcs  = rc3.number_input("GCS",  3,  15, int(SS.v_gcs), key="re_gcs")
        re_n2, _ = calculer_news2(re_fr, re_spo2, o2, re_temp, re_pas, re_fc, re_gcs, SS.v_bpco)
        re_niv, re_just, _ = french_triage(
            SS.motif, SS.det, re_fc, re_pas, re_spo2,
            re_fr, re_gcs, re_temp, age, re_n2, SS.gl)
        st.metric("NEWS2 réévaluation", re_n2, delta=re_n2 - SS.v_news2, delta_color="inverse")
        TRI_CARD_INLINE(re_niv, re_just, re_n2)
        if re_n2 > SS.v_news2:
            AL("NEWS2 en hausse — Réévaluation médicale urgente", "danger")
        elif re_n2 < SS.v_news2:
            AL("NEWS2 en baisse — Amélioration clinique", "success")

        # Timer réévaluation douleur obligatoire (Circulaire belge 2014)
        if SS.t_reev:
            mins = (datetime.now() - SS.t_reev).total_seconds() / 60
            if 25 <= mins <= 35:
                AL("⏱ Réévaluation douleur à 30 min POST-ANTALGIE — Obligatoire (Circulaire 2014)", "warning")
            elif 55 <= mins <= 65:
                AL("⏱ Réévaluation douleur à 60 min POST-ANTALGIE — Obligatoire", "warning")
            delai_cible = {"M": 5, "1": 5, "2": 15, "3A": 30, "3B": 60}.get(SS.niv, 60)
            if mins > delai_cible:
                AL(f"⏱ Délai cible Tri {SS.niv} dépassé ({delai_cible} min) — Relancer le médecin", "danger")

        if st.button("✅ Enregistrer la réévaluation", use_container_width=True):
            SS.reevs.append({
                "h": datetime.now().strftime("%H:%M"),
                "fc": re_fc, "pas": re_pas, "spo2": re_spo2,
                "fr": re_fr, "gcs": re_gcs, "temp": re_temp,
                "n2": re_n2, "niv": re_niv,
            })
            st.success(f"Réévaluation à {SS.reevs[-1]['h']} — Tri {re_niv}")
    CARD_END()

    if SS.reevs:
        COURBE_VITAUX(SS.reevs)

    # Checklist 5B avant injection
    st.divider()
    CARD("Sécurité avant injection — Règle des 5B", "")
    st.caption("AR 78 sur l'exercice infirmier — AFMPS 2019 — Obligatoire avant toute injection")
    para_5b, _  = paracetamol(poids, age, atcd)
    nap_5b, _   = naproxene(poids, age, atcd)
    trad_5b, _  = tramadol(poids, age, atcd)
    dip_5b, _   = piritramide(poids, age, atcd)
    morph_5b, _ = morphine(poids, age, atcd)
    ves_5b, _   = vesiera(poids, age, atcd)
    gluc_5b, _  = glucose(poids, SS.gl, atcd) if SS.gl is not None else (None, None)
    dur_5b  = float(SS.det.get("duree_min", 0) or 0) if SS.det else 0.0
    encours_5b = bool(SS.det.get("en_cours", False)) if SS.det else False
    eme_5b  = protocole_epilepsie_ped(poids, age, dur_5b, encours_5b, atcd)

    med_sel = st.selectbox("Médicament à injecter", [
        "Perfu — Paracétamol IV", "Naproxène PO", "Tradonal® — Tramadol",
        "Dipidolor® — Piritramide", "Morphine IV titrée", "Litican IM (40 mg)",
        "Adrénaline IM (0,5 mg)", "Ceftriaxone IV (2 g)", "Glucose 30 % IV",
        "Salbutamol nébulisation", "Furosémide IV", "Midazolam buccal",
        "Vesiera® — Kétamine perfusion", "Acide tranexamique IV (1 g)", "Autre",
    ], key="re_5b_med")

    doses_default = {
        "Perfu — Paracétamol IV": f"{para_5b['dose_g']} g IV en 15 min" if para_5b else "1 g IV en 15 min",
        "Naproxène PO":           f"{nap_5b['dose_mg']:.0f} mg PO" if nap_5b else "500 mg PO",
        "Tradonal® — Tramadol":   f"{trad_5b['dose_mg']:.0f} mg PO" if trad_5b else "50 mg PO",
        "Dipidolor® — Piritramide": f"{dip_5b['dose_min']:.1f}–{dip_5b['dose_max']:.1f} mg IV lent" if dip_5b else "3–6 mg IV lent",
        "Morphine IV titrée":     f"{morph_5b['dose_min']:.1f}–{morph_5b['dose_max']:.1f} mg IV titré" if morph_5b else "2–7,5 mg IV titré",
        "Litican IM (40 mg)":     "40 mg IM",
        "Adrénaline IM (0,5 mg)": "0,5 mg IM cuisse antéro-latérale",
        "Ceftriaxone IV (2 g)":   "2 g IV en 3-5 min",
        "Glucose 30 % IV":        str(gluc_5b["vol"]) if gluc_5b else "Selon glycémie mesurée",
        "Salbutamol nébulisation": "2,5–5 mg nébulisation",
        "Furosémide IV":          "40–80 mg IV lent",
        "Midazolam buccal":       str(eme_5b["midazolam_buccal"]["dose"]),
        "Vesiera® — Kétamine perfusion": str(ves_5b["dose"]) if ves_5b else "Selon protocole algologue",
        "Acide tranexamique IV (1 g)": "1 g IV en 10 min",
        "Autre":                  "À compléter",
    }
    dose_pre = st.text_input("Dose calculée", value=doses_default.get(med_sel, ""), key="re_5b_dose")
    voie_pre = st.selectbox("Voie", ["IV", "IM", "SC", "IN (intranasale)", "Buccale", "Nébulisation", "PO"], key="re_5b_voie")
    CHECKLIST_5B(
        medicament=med_sel, dose=dose_pre, voie=voie_pre,
        poids=poids, uid=SS.uid_cur or SS.sid,
    )
    CARD_END()
    DISC()


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 7 — HISTORIQUE / REGISTRE
# ═══════════════════════════════════════════════════════════════════════════════
with T[7]:
    reg = charger_registre()
    if reg:
        CARD("Statistiques session", "")
        s1, s2, s3 = st.columns(3)
        s1.metric("Patients", len(reg))
        s2.metric("Critiques (Tri M/1/2)", sum(1 for r in reg if r.get("niv") in ("M", "1", "2")))
        s3.metric("NEWS2 moyen", round(sum(r.get("n2", 0) for r in reg) / len(reg), 1))
        CARD_END()

    CARD("Registre session (RGPD — anonyme)", "")
    if not reg:
        st.info("Aucun patient enregistré dans cette session")
    else:
        for r in reg[:20]:
            c = st.columns([1, 3, 1, 1])
            c[0].caption(r.get("heure", "")[-5:])
            c[1].write(r.get("motif", ""))
            c[2].write(f"**Tri {r.get('niv', '')}**")
            c[3].caption(r.get("uid", ""))
    CARD_END()

    CARD("Export RGPD", "")
    if reg:
        out = io.StringIO()
        w   = csv_mod.writer(out)
        w.writerow(["uid", "heure", "motif", "niv", "n2", "fc", "pas", "spo2", "fr", "temp", "gcs", "op"])
        for r in reg:
            w.writerow([r.get(k, "") for k in ["uid", "heure", "motif", "niv", "n2", "fc", "pas", "spo2", "fr", "temp", "gcs", "op"]])
        st.download_button("📥 Télécharger CSV", data=out.getvalue(),
            file_name=f"akir_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv", use_container_width=True)

    if st.button("🔐 Vérifier intégrité audit", use_container_width=True):
        audit = audit_verifier_integrite()
        AL(audit["message"], "success" if audit["ok"] else "danger")
    CARD_END()
    DISC()


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 8 — TRANSMISSION SBAR
# ═══════════════════════════════════════════════════════════════════════════════
with T[8]:
    CARD("Transmission SBAR", "")
    if not SS.niv:
        AL("Calculer d'abord le triage (onglet Triage ou Tri Rapide)", "info")
    else:
        sbar = build_sbar(
            age, SS.motif, SS.cat, atcd, alg, o2,
            SS.v_temp, SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr, SS.v_gcs,
            SS.eva, SS.v_news2, SS.niv, SS.just, SS.crit,
            SS.op or "IAO", SS.gl,
        )
        SBAR_RENDER(sbar)
    CARD_END()
    DISC()
