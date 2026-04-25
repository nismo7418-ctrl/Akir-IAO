# streamlit_app.py — AKIR-IAO v19.0 — Système Expert Grade Hospitalier
# Développeur : Ismail Ibn-Daifa — Hainaut, Wallonie, Belgique
# Architecture : Modulaire — FRENCH SFMU V1.1 — BCFI — RGPD

import streamlit as st
import uuid, io, csv as csv_mod
from datetime import datetime

# ── Configuration page ────────────────────────────────────────────────────────
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
    calculer_gcs, calculer_qsofa, calculer_timi, evaluer_fast,
    calculer_algoplus, evaluer_cfs, calculer_heart,
    calculer_wells_tvp, calculer_wells_ep, calculer_nihss,
    calculer_sofa_partiel, calculer_curb65,
    regle_ottawa_cheville, regle_canadian_ct,
)
from clinical.vitaux import si, sipa
from clinical.pharmaco import (
    paracetamol, naproxene, ketorolac, tramadol, piritramide, morphine,
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
    EVA_WIDGET_COMPLET, SCHEMA_BRULURES,
    QUESTIONS_AVANCEES, CHECKLIST_5B,
    COURBE_VITAUX, PRESCRIPTIONS_ANTICIPEES,
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
# SESSION STATE — Source de vérité unique pour toutes les variables partagées
# RÈGLE : Toute variable lue dans plus d'un onglet DOIT passer par session_state
# ═══════════════════════════════════════════════════════════════════════════════

_DEF = {
    # Identité session
    "sid":    lambda: str(uuid.uuid4())[:8].upper(),
    "op":     "",
    # Chronomètre
    "t_arr":  None,
    "t_cont": None,
    # Vitaux — persistés entre onglets (correction bug critique)
    "v_temp": 37.0,
    "v_fc":   80,
    "v_pas":  120,
    "v_spo2": 98,
    "v_fr":   16,
    "v_gcs":  15,
    "v_news2":0,
    "v_bpco": False,
    # Triage
    "motif":  "",
    "cat":    "",
    "det":    {},
    "eva":    0,
    "gl":     None,
    "niv":    "",
    "just":   "",
    "crit":   "",
    # Réévaluation
    "reevs":  [],
    "t_reev": None,
    # Historique
    "histo":  [],
    "uid_cur":None,
}
for k, v in _DEF.items():
    if k not in st.session_state:
        st.session_state[k] = v() if callable(v) else v

SS = st.session_state  # Raccourci global


def _sync_state_from_widget(widget_key: str, state_key: str) -> None:
    """Recopie la valeur d'un widget vers l'etat canonique."""
    SS[state_key] = SS[widget_key]


def _mirror_state_to_widget(widget_key: str, state_key: str) -> None:
    """Aligne un widget sur l'etat canonique avant son instanciation."""
    SS[widget_key] = SS[state_key]

# ── En-tête ───────────────────────────────────────────────────────────────────
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
# SIDEBAR — Patient + Opérateur
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    SEC("Opérateur IAO")
    op_in = st.text_input("Code opérateur", value=SS.op, max_chars=10, placeholder="IAO01")
    if op_in: SS.op = op_in.upper()

    SEC("Chronomètre")
    ca, cb = st.columns(2)
    if ca.button("⏱ Arrivée", use_container_width=True):
        SS.t_arr  = datetime.now()
        SS.histo  = []; SS.reevs = []
    if cb.button("👨‍⚕️ Contact", use_container_width=True):
        SS.t_cont = datetime.now()
    if SS.t_arr:
        el = (datetime.now() - SS.t_arr).total_seconds()
        m, s_ = divmod(int(el), 60)
        col = "#EF4444" if el>600 else ("#F59E0B" if el>300 else "#22C55E")
        H(f'<div style="text-align:center;font-family:monospace;font-size:2rem;'
          f'font-weight:700;color:{col};">{m:02d}:{s_:02d}</div>')

    SEC("Patient")
    age = st.number_input("Âge (ans)", 0, 120, 45, key="p_age")
    if age == 0:
        am = st.number_input("Âge en mois", 0, 11, 3, key="p_am")
        age = round(am / 12.0, 4)
        AL(f"Nourrisson {am} mois — seuils pédiatriques", "info")
    poids = st.number_input("Poids (kg)", 1, 250, 70, key="p_kg")
    taille = st.number_input("Taille (cm)", 50, 220, 170, key="p_taille")

    # IMC
    if taille > 0 and age >= 18:
        imc = round(poids / (taille/100)**2, 1)
        if   imc < 18.5: AL(f"IMC {imc} — Insuffisance pondérale", "warning")
        elif imc < 25.0: st.caption(f"IMC {imc} — Normal")
        elif imc < 30.0: AL(f"IMC {imc} — Surpoids", "info")
        elif imc < 40.0: AL(f"IMC {imc} — Obésité", "warning")
        else:             AL(f"IMC {imc} — Obésité morbide ≥ 40 — Adapter doses opioïdes", "danger")

    # ATCD et allergies — propagés à tous les onglets via SS
    atcd = st.multiselect("Antécédents pertinents", ATCD, key="p_atcd")
    alg  = st.text_input("Allergies", key="p_alg", placeholder="ex: Pénicilline")
    o2   = st.checkbox("O₂ supplémentaire", key="p_o2")

    # Alertes ATCD critiques immédiatement visibles
    if "IMAO (inhibiteurs MAO)" in atcd:
        AL("IMAO — Tramadol INTERDIT", "danger")
    if "Immunodépression" in atcd or "Chimiothérapie en cours" in atcd:
        AL("Immunodéprimé — Seuil alerte abaissé", "warning")
    if "Drépanocytose" in atcd:
        AL("Drépanocytose — Morphine titrée précoce si douleur ≥ 6", "warning")

    SEC("Session RGPD")
    st.caption(f"Session : {SS.sid}")
    if st.button("🔄 Nouvelle session", use_container_width=True):
        for k, v in _DEF.items():
            SS[k] = v() if callable(v) else v
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# ONGLETS
# ═══════════════════════════════════════════════════════════════════════════════
T = st.tabs([
    "Tri Rapide", "Vitaux & GCS", "Anamnèse", "Triage",
    "Scores Cliniques", "Pharmacie", "Réévaluation",
    "Historique", "Transmission SBAR",
])

# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 1 — TRI RAPIDE
# ═══════════════════════════════════════════════════════════════════════════════
with T[0]:
    CARD("Constantes vitales", "")
    c1,c2,c3 = st.columns(3)
    _mirror_state_to_widget("r_t", "v_temp")
    _mirror_state_to_widget("r_fc", "v_fc")
    _mirror_state_to_widget("r_pas", "v_pas")
    _mirror_state_to_widget("r_sp", "v_spo2")
    _mirror_state_to_widget("r_fr", "v_fr")
    # Écriture dans SS pour persistance inter-onglets
    SS.v_temp = c1.number_input("Température (°C)", min_value=30.0, max_value=45.0, step=0.1,
                                key="r_t", on_change=_sync_state_from_widget, args=("r_t", "v_temp"))
    SS.v_fc   = c2.number_input("FC (bpm)", min_value=20, max_value=220,
                                key="r_fc", on_change=_sync_state_from_widget, args=("r_fc", "v_fc"))
    SS.v_pas  = c3.number_input("PAS (mmHg)", min_value=40, max_value=260,
                                key="r_pas", on_change=_sync_state_from_widget, args=("r_pas", "v_pas"))
    c4,c5,c6 = st.columns(3)
    SS.v_spo2 = c4.number_input("SpO2 (%)", min_value=50, max_value=100,
                                key="r_sp", on_change=_sync_state_from_widget, args=("r_sp", "v_spo2"))
    SS.v_fr   = c5.number_input("FR (/min)", min_value=5, max_value=60,
                                key="r_fr", on_change=_sync_state_from_widget, args=("r_fr", "v_fr"))
    SS.v_gcs  = c6.number_input("GCS (3-15)", 3,  15, int(SS.v_gcs),  key="r_gcs")
    CARD_END()

    CARD("Motif & Sécurité", "")
    SS.v_bpco = st.checkbox("Patient BPCO connu ?", key="r_bp", value=("BPCO" in atcd))
    if SS.v_bpco:
        BPCO_WIDGET(True)
    SS.v_news2, nw = calculer_news2(SS.v_fr, SS.v_spo2, o2, SS.v_temp,
                                     SS.v_pas, SS.v_fc, SS.v_gcs, SS.v_bpco)
    for w in nw: AL(w, "warning")
    # @st.fragment — mise à jour instantanée sans rechargement
    GAUGE(SS.v_news2, SS.v_bpco)
    SS.motif = st.selectbox("Motif de recours", MOTIFS_RAPIDES, key="r_mot")
    SS.cat   = "Tri rapide"
    SS.eva   = int(st.select_slider("EVA", [str(i) for i in range(11)], "0", key="r_eva"))
    det      = {"eva": SS.eva, "atcd": atcd}
    det["purpura"] = st.checkbox("Purpura non effaçable (test du verre)", key="r_pur")
    if det.get("purpura"):
        PURPURA(det)
    gl_r = GLYC_WIDGET("r_gl", "Glycémie capillaire (mg/dl)")
    if gl_r:
        det["glycemie_mgdl"] = gl_r
        SS.gl = gl_r

    if st.button("⚡ Calculer le triage", type="primary", use_container_width=True):
        N2_BANNER(SS.v_news2)
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
    CARD_END()
    VITAUX(SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr, SS.v_temp, SS.v_gcs, SS.v_bpco)

# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 2 — VITAUX & GCS
# ═══════════════════════════════════════════════════════════════════════════════
with T[1]:
    CARD("Paramètres vitaux", "")
    v1,v2,v3 = st.columns(3)
    _mirror_state_to_widget("v_t", "v_temp")
    _mirror_state_to_widget("v_sp", "v_spo2")
    SS.v_temp = v1.number_input("Température (°C)", min_value=30.0, max_value=45.0, step=0.1,
                                key="v_t", on_change=_sync_state_from_widget, args=("v_t", "v_temp"))
    fc_v2 = v1.number_input("FC (bpm)", min_value=20, max_value=220, key="v_fc")
    pas_v2 = v2.number_input("PAS (mmHg)", min_value=40, max_value=260, key="v_pas")
    SS.v_spo2 = v2.number_input("SpO2 (%)", min_value=50, max_value=100,
                                key="v_sp", on_change=_sync_state_from_widget, args=("v_sp", "v_spo2"))
    fr_v2 = v3.number_input("FR (/min)", min_value=5, max_value=60, key="v_fr")
    CARD_END()

    CARD("Glasgow Coma Scale", "")
    g1,g2,g3 = st.columns(3)
    gy = g1.selectbox("Yeux (Y)", [4,3,2,1], key="v_gy",
        format_func=lambda x:{4:"4–Spontanée",3:"3–À la voix",2:"2–Douleur",1:"1–Aucune"}[x])
    gv = g2.selectbox("Verbal (V)", [5,4,3,2,1], key="v_gv",
        format_func=lambda x:{5:"5–Orientée",4:"4–Confuse",3:"3–Mots",2:"2–Sons",1:"1–Aucune"}[x])
    gm = g3.selectbox("Moteur (M)", [6,5,4,3,2,1], key="v_gm",
        format_func=lambda x:{6:"6–Obéit",5:"5–Localise",4:"4–Évitement",3:"3–Flexion",2:"2–Extension",1:"1–Aucune"}[x])
    SS.v_gcs, _ = calculer_gcs(gy, gv, gm)
    if SS.v_gcs <= 8:
        AL(f"GCS {SS.v_gcs}/15 — Coma grave — Protection VAS urgente", "danger")
    elif SS.v_gcs <= 12:
        AL(f"GCS {SS.v_gcs}/15 — Altération modérée", "warning")
    st.metric("Score GCS", f"{SS.v_gcs} / 15")
    CARD_END()

    SS.v_news2, nw = calculer_news2(SS.v_fr, SS.v_spo2, o2, SS.v_temp,
                                     SS.v_pas, SS.v_fc, SS.v_gcs, SS.v_bpco)
    for w in nw: AL(w, "warning")
    GAUGE(SS.v_news2, SS.v_bpco)
    N2_BANNER(SS.v_news2)
    VITAUX(SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr, SS.v_temp, SS.v_gcs, SS.v_bpco)

    sh_val = si(SS.v_fc, SS.v_pas)
    AL(f"Shock Index {sh_val}" + (" — CHOC PROBABLE" if sh_val >= 1 else " — Normal"),
       "danger" if sh_val >= 1 else ("warning" if sh_val >= 0.8 else "success"))
    DISC()

# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 3 — ANAMNÈSE — Arbres de décision
# ═══════════════════════════════════════════════════════════════════════════════
with T[2]:
    # ── Évaluation de la douleur — EVA visuel + PQRST ─────────────────────
    non_comm = ("Démence" in atcd or "Insuffisance mentale" in atcd
                or (age >= 75 and SS.v_gcs < 15))
    eva_result = EVA_WIDGET_COMPLET(
        key_prefix="ana", age=age, non_communicant=non_comm
    )
    SS.eva = eva_result.get("eva", 0)
    SS.det.update({"eva": SS.eva, "pqrst": eva_result.get("pqrst",{}), "atcd": atcd})

    # ── Motif de recours ───────────────────────────────────────────────────
    CARD("Motif de recours", "")
    SS.cat   = st.selectbox("Catégorie", list(MOTS_CAT.keys()), key="a_cat")
    SS.motif = st.selectbox("Motif principal", MOTS_CAT[SS.cat], key="a_mot")
    CARD_END()

    # ── Schéma des brûlures si motif brûlure ──────────────────────────────
    if "Brulure" in SS.motif or "brulure" in SS.motif.lower():
        brul_result = SCHEMA_BRULURES(poids=poids, age=age)
        SS.det.update({
            "surface_pct": brul_result["surface_pct"],
            "baux":        brul_result["baux"],
            "profondeur":  brul_result["profondeur"],
        })

    # ── Questions discriminantes avancées ──────────────────────────────────
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

    # ── Prescriptions anticipées IAO ───────────────────────────────────────
    if SS.motif:
        pa_result = PRESCRIPTIONS_ANTICIPEES(
            motif=SS.motif, niv=SS.niv or "3B",
            poids=poids, age=age, atcd=atcd,
            eva=SS.eva, spo2=SS.v_spo2, pas=SS.v_pas,
        )
        if pa_result:
            SS.det["pa_tracabilite"] = pa_result

# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 4 — TRIAGE
# ═══════════════════════════════════════════════════════════════════════════════
with T[3]:
    if not SS.motif: SS.motif = "Fievre"; SS.cat = "Infectiologie"
    SS.v_news2, nw = calculer_news2(SS.v_fr, SS.v_spo2, o2, SS.v_temp,
                                     SS.v_pas, SS.v_fc, SS.v_gcs, SS.v_bpco)
    for w in nw: AL(w, "warning")

    det = SS.det or {}
    if not det.get("glycemie_mgdl") and not SS.gl:
        gl_t = GLYC_WIDGET("t_gl", "Glycémie capillaire (mg/dl)")
        if gl_t:
            det["glycemie_mgdl"] = gl_t
            SS.gl = gl_t; SS.det = det
    gl_t = det.get("glycemie_mgdl") or SS.gl

    SS.niv, SS.just, SS.crit = french_triage(
        SS.motif, det, SS.v_fc, SS.v_pas, SS.v_spo2,
        SS.v_fr, SS.v_gcs, SS.v_temp, age, SS.v_news2, gl_t,
    )
    N2_BANNER(SS.v_news2)
    PURPURA(det)
    GAUGE(SS.v_news2, SS.v_bpco)
    TRI_CARD_INLINE(SS.niv, SS.just, SS.v_news2)
    st.caption(f"Critère : {SS.crit}")

    D, A = verifier_coherence(SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr,
                               SS.v_gcs, SS.v_temp, SS.eva, SS.motif,
                               atcd, det, SS.v_news2, gl_t)
    for d in D: AL(d, "danger")
    for a in A: AL(a, "warning")

    if st.button("💾 Enregistrer ce patient", type="primary", use_container_width=True):
        uid = enregistrer_patient({
            "motif": SS.motif, "cat": SS.cat, "niv": SS.niv, "n2": SS.v_news2,
            "fc": SS.v_fc, "pas": SS.v_pas, "spo2": SS.v_spo2, "fr": SS.v_fr,
            "temp": SS.v_temp, "gcs": SS.v_gcs, "op": SS.op,
        })
        SS.uid_cur = uid
        SS.reevs   = []
        SS.t_reev  = datetime.now()
        SS.histo.insert(0, {"uid": uid, "h": datetime.now().strftime("%H:%M"),
                             "motif": SS.motif, "niv": SS.niv, "n2": SS.v_news2})
        st.success(f"Patient enregistré — UID : {uid}")
    TRI_BANNER_FIXED(SS.niv, SS.just, SS.v_news2)
    DISC()

# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 5 — SCORES CLINIQUES — 3 sous-onglets
# ═══════════════════════════════════════════════════════════════════════════════
with T[4]:
    S = st.tabs(["Adulte — Cardio / Neuro", "Infectio / Respiratoire", "Imagerie & Règles"])

    with S[0]:
        sc_l, sc_r = st.columns(2)
        with sc_l:
            CARD("qSOFA — Dépistage sepsis","")
            qs,qp,qw = calculer_qsofa(SS.v_fr or 16, SS.v_gcs or 15, SS.v_pas or 120)
            for w in qw: AL(w,"warning")
            qs_css = "si-c" if qs>=2 else "si-ok"
            H(f'<div class="si-box"><div class="si-l">qSOFA</div>'
              f'<div class="si-v {qs_css}">{qs}/3</div>'
              f'<div class="si-l">{"Sepsis probable" if qs>=2 else "Risque faible"}</div></div>')
            if qs >= 2: AL("Activer bundle sepsis 1 h — onglet Pharmacie","danger")
            CARD_END()

        with sc_r:
            CARD("Score HEART — Douleur thoracique","")
            st.caption("Six AJ et al. Heart 2010 — Supérieur au TIMI aux urgences")
            h1,h2=st.columns(2)
            h_hist=h1.select_slider("Histoire",[0,1,2],key="ht_h",
                format_func=lambda x:{0:"0–Peu",1:"1–Modéré",2:"2–Très suspect"}[x])
            h_ecg =h2.select_slider("ECG",[0,1,2],key="ht_e",
                format_func=lambda x:{0:"0–Normal",1:"1–Non spéc.",2:"2–Déviation ST"}[x])
            h_age =h1.select_slider("Âge",[0,1,2],key="ht_a",
                format_func=lambda x:{0:"0–<45",1:"1–45-64",2:"2–≥65"}[x])
            h_risk=h2.select_slider("FRCV",[0,1,2],key="ht_r",
                format_func=lambda x:{0:"0–Aucun",1:"1–1-2",2:"2–≥3/ATCD"}[x])
            h_trop=h1.select_slider("Troponine",[0,1,2],key="ht_t",
                format_func=lambda x:{0:"0–Normale",1:"1–1-3×",2:"2–>3×"}[x])
            hsc,hlbl,hcss=calculer_heart(h_hist,h_ecg,h_age,h_risk,h_trop)
            hm={"success":"si-ok","warning":"si-w","danger":"si-c"}
            H(f'<div class="si-box"><div class="si-l">HEART</div>'
              f'<div class="si-v {hm.get(hcss,"si-ok")}">{hsc}/10</div>'
              f'<div class="si-l" style="font-size:.6rem;">{hlbl}</div></div>')
            CARD_END()

        CARD("Score TIMI — SCA NSTEMI","")
        ti1,ti2=st.columns(2)
        ta=ti1.checkbox("Âge ≥ 65 ans",key="ti_a",value=age>=65)
        tf=ti1.number_input("Nb FRCV",0,5,0,key="ti_f")
        tstT=ti2.checkbox("Sténose ≥ 50 %",key="ti_s")
        taspi=ti1.checkbox("Aspirine 7 j",key="ti_asp")
        ttr=ti2.checkbox("Troponine +",key="ti_tr")
        tdst=ti1.checkbox("Déviation ST",key="ti_d")
        tcris=ti2.checkbox("≥ 2 crises/24 h",key="ti_c")
        tsc,_=calculer_timi(age,int(tf),tstT,taspi,ttr,tdst,int(tcris)*2)
        ti_l="Risque élevé" if tsc>=5 else ("Intermédiaire" if tsc>=3 else "Faible")
        ti_c="si-c" if tsc>=5 else ("si-w" if tsc>=3 else "si-ok")
        H(f'<div class="si-box"><div class="si-l">TIMI</div>'
          f'<div class="si-v {ti_c}">{tsc}/7</div>'
          f'<div class="si-l">{ti_l}</div></div>')
        CARD_END()

        sc_l2,sc_r2=st.columns(2)
        with sc_l2:
            CARD("FAST — Dépistage AVC","")
            f1,f2,f3,f4=st.columns(4)
            ff=f1.checkbox("Face",key="sf"); fa=f2.checkbox("Bras",key="sa")
            fs=f3.checkbox("Langage",key="ss"); ft=f4.checkbox("Début",key="st2")
            fsc,fi,fal=evaluer_fast(ff,fa,fs,ft)
            AL(fi,"danger" if fal else ("warning" if fsc>=1 else "success"))
            CARD_END()

        with sc_r2:
            CARD("Algoplus — Douleur non communicant","")
            al1,al2,al3,al4,al5=st.columns(5)
            av=al1.checkbox("Visage",key="ag_v"); ar=al2.checkbox("Regard",key="ag_r")
            ap=al3.checkbox("Plaintes",key="ag_p"); aac=al4.checkbox("Corps",key="ag_ac")
            aco=al5.checkbox("Comport.",key="ag_co")
            asc,ai,acss,_=calculer_algoplus(av,ar,ap,aac,aco)
            AL(f"Algoplus {asc}/5 — {ai}",acss)
            CARD_END()

        CARD("CFS — Fragilité","")
        cfs_v=st.slider("Score CFS (1-9)",1,9,3,key="cfs")
        st.caption(CFS_LBL.get(cfs_v,""))
        cfl,cfc,cfr=evaluer_cfs(cfs_v)
        AL(f"CFS {cfs_v} — {cfl}",cfc)
        if cfr: AL("CFS ≥ 5 — Envisager remontée d'un niveau de triage","warning")
        CARD_END()

    with S[1]:
        CARD("SOFA partiel — Défaillance d'organe","")
        sf1,sf2=st.columns(2)
        sf_vaso=sf1.checkbox("Vasopresseurs",key="sf_v")
        sf_pao =sf1.number_input("PaO2/FiO2 (0=non)",0,600,0,key="sf_p")
        sf_plaq=sf2.number_input("Plaquettes ×10³/µl (0=non)",0,700,0,key="sf_pl")
        sf_cr  =sf2.number_input("Créatinine µmol/l (0=non)",0,1500,0,key="sf_cr")
        sf_sc,sf_notes=calculer_sofa_partiel(
            SS.v_pas or 120, SS.v_gcs or 15, sf_vaso,
            sf_pao if sf_pao>0 else None,
            sf_plaq if sf_plaq>0 else None,
            sf_cr if sf_cr>0 else None)
        AL("SOFA sévère — USI" if sf_sc>12 else ("Modéré — USI à discuter" if sf_sc>6 else "Léger"),
           "danger" if sf_sc>12 else "warning" if sf_sc>6 else "success")
        st.metric("SOFA partiel",f"{sf_sc}/24")
        for n in sf_notes: AL(n,"warning")
        CARD_END()

        CARD("CURB-65 — Pneumonie communautaire","")
        cb1,cb2=st.columns(2)
        cb_c=cb1.checkbox("Confusion",key="cb_c")
        cb_u=cb1.checkbox("Urée > 7 mmol/l",key="cb_u")
        cb_f=cb1.checkbox(f"FR ≥ 30/min",key="cb_f",value=(SS.v_fr or 0)>=30)
        cb_p=cb2.checkbox("PAS < 90 mmHg",key="cb_p",value=(SS.v_pas or 120)<90)
        cb_a=cb2.checkbox("Âge ≥ 65 ans",key="cb_a",value=age>=65)
        cbsc,cblbl,cbcss=calculer_curb65(cb_c,cb_u,cb_f,cb_p,cb_a)
        AL(cblbl,cbcss); st.metric("CURB-65",f"{cbsc}/5")
        CARD_END()

        CARD("qSOFA + SOFA → Sepsis Bundle","")
        if qs >= 2:
            AL("qSOFA ≥ 2 + SOFA — Activer le bundle sepsis 1 h (onglet Pharmacie)","danger")
        CARD_END()

    with S[2]:
        CARD("Règles d'Ottawa — Cheville","")
        ot1,ot2=st.columns(2)
        ot_ap=ot1.checkbox("Pas d'appui (4 pas)",key="ot_ap")
        ot_mm=ot1.checkbox("Douleur bord post. malléole médiale",key="ot_mm")
        ot_tl=ot2.checkbox("Douleur tip malléole latérale",key="ot_tl")
        ot_5m=ot1.checkbox("Douleur base 5e métatarse",key="ot_5m")
        ot_nv=ot2.checkbox("Douleur naviculaire",key="ot_nv")
        ot_res,ot_lbl,ot_css=regle_ottawa_cheville(ot_ap,ot_mm,ot_tl,ot_5m,ot_nv)
        AL(ot_lbl,ot_css)
        CARD_END()

        CARD("Règle Canadienne — TDM cérébral (GCS 13-15)","")
        AL("Non applicable : GCS < 13 | coagulopathie | convulsion | < 16 ans","warning")
        cc1,cc2=st.columns(2)
        cc_g=cc1.checkbox("GCS < 15 à 2 h",key="cc_g")
        cc_s=cc1.checkbox("Suspicion fracture ouverte",key="cc_s")
        cc_v=cc1.checkbox("Vomissements ≥ 2",key="cc_v")
        cc_a=cc2.checkbox("Âge ≥ 65 ans",key="cc_a",value=age>=65)
        cc_am=cc2.checkbox("Amnésie ≥ 30 min",key="cc_am")
        cc_m=cc2.checkbox("Mécanisme dangereux",key="cc_m")
        cc_res,cc_lbl,cc_css=regle_canadian_ct(cc_g,cc_s,cc_v,cc_a,cc_am,cc_m)
        AL(cc_lbl,cc_css)
        CARD_END()

    DISC()

# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 6 — PHARMACIE — Liaisons ATCD complètes
# ═══════════════════════════════════════════════════════════════════════════════
with T[5]:
    gl_ph = SS.det.get("glycemie_mgdl") if SS.det else None
    gl_ph = gl_ph or SS.gl

    # Bandeau patient
    H(f"""<div style="background:linear-gradient(135deg,#004A99,#0066CC);
        color:#fff;border-radius:10px;padding:12px 18px;margin-bottom:12px;
        display:flex;justify-content:space-between;align-items:center;">
      <div>
        <div style="font-size:.7rem;opacity:.8;">Doses calculées pour</div>
        <div style="font-size:1.4rem;font-weight:800;">{poids} kg — {age} ans</div>
      </div>
      <div style="font-size:.72rem;opacity:.8;text-align:right;">
        ATCD actifs : {len(atcd)} | Allergies : {alg or 'aucune'}
      </div>
    </div>""")

    # Alertes ATCD pharmacologiques globales
    if "IMAO (inhibiteurs MAO)" in atcd:
        AL("IMAO — TRAMADOL CONTRE-INDIQUÉ ABSOLU dans cette session", "danger")
    if "Insuffisance cardiaque" in atcd:
        AL("Insuffisance cardiaque — Furosémide prioritaire / Volume remplissage réduit 15 ml/kg", "warning")
    if gl_ph is None:
        AL("Glycémie non saisie — Glucose 30 % désactivé", "warning")

    para_rx, para_err = paracetamol(poids, age, atcd)
    nap_rx, nap_err = naproxene(poids, age, atcd)
    trad_rx, trad_err = tramadol(poids, age, atcd)
    dip_rx, dip_err = piritramide(poids, age, atcd)
    morph_rx, morph_err = morphine(poids, age, atcd)
    ves_rx, ves_err = vesiera(poids, age, atcd)

    # ── Protocole EVA ────────────────────────────────────────────────────
    CARD("Antalgie — Protocole ÉVA / OMS","")
    ev_ph = int(st.select_slider("ÉVA actuelle",
        [str(i) for i in range(11)], str(SS.eva), key="ph_eva"))
    prt = protocole_eva(ev_ph, poids, age, atcd, gl_ph)
    for al_msg, al_css in prt.get("als",[]): AL(al_msg, al_css)
    for rec in prt.get("recs",[]):
        RX(rec["nom"], rec["dose"],
           [rec.get("admin",""), rec.get("note","")],
           rec["ref"], rec.get("palier","2"),
           rec.get("alerts",[]))
    CARD_END()

    pa1, pa2 = st.columns(2)
    with pa1:
        CARD("Perfu — Paracétamol IV", "")
        if para_err:
            AL(para_err, "danger")
        elif para_rx:
            for al_m, al_c in para_rx.get("alerts", []): AL(al_m, al_c)
            RX("Perfu — Paracétamol IV", f"{para_rx['dose_g']} g",
               [para_rx["admin"], para_rx["note"]], para_rx["ref"], "1",
               para_rx.get("alerts", []))
        CARD_END()

        CARD("Tradonal® — Tramadol", "")
        if trad_err:
            AL(trad_err, "danger" if "contre-indiqu" in trad_err.lower() else "warning")
        elif trad_rx:
            for al_m, al_c in trad_rx.get("alerts", []): AL(al_m, al_c)
            RX("Tradonal® — Tramadol", f"{trad_rx['dose_mg']:.0f} mg",
               [trad_rx["admin"], trad_rx["note"]], trad_rx["ref"], "2",
               trad_rx.get("alerts", []))
        CARD_END()

        CARD("Dipidolor® — Piritramide", "")
        if dip_err:
            AL(dip_err, "warning")
        elif dip_rx:
            for al_m, al_c in dip_rx.get("alerts", []): AL(al_m, al_c)
            RX("Dipidolor® — Piritramide",
               f"{dip_rx['dose_min']:.1f}-{dip_rx['dose_max']:.1f} mg",
               [dip_rx["admin"], dip_rx["note"]], dip_rx["ref"], "3",
               dip_rx.get("alerts", []))
        CARD_END()

    with pa2:
        CARD("Naproxène PO", "")
        if nap_err:
            AL(nap_err, "warning")
        elif nap_rx:
            for al_m, al_c in nap_rx.get("alerts", []): AL(al_m, al_c)
            RX("Naproxène PO", f"{nap_rx['dose_mg']:.0f} mg",
               [nap_rx["admin"], nap_rx["note"]], nap_rx["ref"], "1",
               nap_rx.get("alerts", []))
        CARD_END()

        CARD("Morphine IV titrée", "")
        if morph_err:
            AL(morph_err, "warning")
        elif morph_rx:
            for al_m, al_c in morph_rx.get("alerts", []): AL(al_m, al_c)
            RX("Morphine IV titrée",
               f"{morph_rx['dose_min']:.1f}-{morph_rx['dose_max']:.1f} mg",
               [morph_rx["admin"], morph_rx["note"]], morph_rx["ref"], "3",
               morph_rx.get("alerts", []))
        CARD_END()

        CARD("Vesiera® — Kétamine perfusion", "")
        if ves_err:
            AL(ves_err, "warning")
        elif ves_rx:
            for al_m, al_c in ves_rx.get("alerts", []): AL(al_m, al_c)
            RX("Vesiera® — Kétamine perfusion", str(ves_rx["dose"]),
               [ves_rx["admin"], ves_rx["note"]], ves_rx["ref"], "3",
               ves_rx.get("alerts", []))
        CARD_END()

    CARD("Midazolam / État de mal épileptique", "")
    em1, em2 = st.columns(2)
    eme_duree = em1.number_input(
        "Durée de crise (min)",
        0.0, 120.0, float(SS.det.get("duree_min", 0) or 0), 0.5,
        key="ph_eme_duree",
    )
    eme_en_cours = em2.checkbox(
        "Crise en cours",
        value=bool(SS.det.get("en_cours", False)),
        key="ph_eme_encours",
    )
    eme = protocole_epilepsie_ped(poids, age, eme_duree, eme_en_cours, atcd, gl=gl_ph)
    eme_level = "danger" if "EME" in eme["stage"] else ("warning" if "Crise" in eme["stage"] else "info")
    AL(f"Stade clinique : {eme['stage']}", eme_level)
    for al_m, al_c in eme.get("alerts", []):
        AL(al_m, al_c)
    mid = eme["midazolam_buccal"]
    RX(mid["med"], mid["dose"],
       [mid["admin"], f"Volume : {mid['volume']}", mid["note"]],
       mid["ref"], "U")
    st.caption("Chronologie proposée")
    for step_lbl, step_txt in eme.get("timeline", []):
        H(f'<div style="padding:7px 10px;margin:4px 0;border-left:3px solid #475569;'
          f'background:#111827;border-radius:0 6px 6px 0;font-size:.74rem;">'
          f'<strong>{step_lbl}</strong> — {step_txt}</div>')
    eleft, eright = st.columns(2)
    with eleft:
        for alt in eme.get("alternatives", []):
            RX(alt["med"], alt["dose"], [alt["admin"], alt["note"]], alt["ref"], "2")
    with eright:
        for rec in eme.get("second_line", []):
            RX(rec["med"], rec["dose"], [rec["admin"], rec["note"]], rec["ref"], "3")
    CARD_END()

    # ── Urgences vitales ─────────────────────────────────────────────────
    ph1,ph2=st.columns(2)
    with ph1:
        CARD("Adrénaline IM — Anaphylaxie","")
        ar,ae=adrenaline(poids, atcd)
        if ae: AL(ae,"danger")
        else:
            for al_m,al_c in ar.get("alerts",[]): AL(al_m,al_c)
            RX("Adrénaline IM (Sterop 1 mg/ml)",f"{ar['dose_mg']} mg",
               [ar["voie"],ar["note"],ar["rep"]],ar["ref"],"U",ar.get("alerts",[]))
        CARD_END()

    with ph2:
        CARD("Naloxone IV — Antidote opioïdes","")
        dep_ph=st.checkbox("Patient dépendant aux opioïdes",key="ph_dep")
        nr,_=naloxone(poids, age, dep_ph, atcd)
        if nr:
            for al_m,al_c in nr.get("alerts",[]): AL(al_m,al_c)
            RX("Naloxone IV (Narcan)",f"{nr['dose']} mg",
               [nr["admin"],nr["note"]],nr["ref"],"U",nr.get("alerts",[]))
        CARD_END()

    # ── Glucose ──────────────────────────────────────────────────────────
    CARD("Glucose 30 % IV — Hypoglycémie","")
    if gl_ph is None:
        RX_LOCK("Glycémie capillaire non mesurée — Saisir la glycémie d'abord")
    else:
        gr,ge=glucose(poids, gl_ph, atcd)
        if ge: AL(ge,"danger" if ("Hypoglycémie" not in ge and "Hypoglycemie" not in ge) else "info")
        else:
            for al_m,al_c in gr.get("alerts",[]): AL(al_m,al_c)
            RX("Glucose 30 % IV",f"{gr['dose_g']} g",
               [gr["vol"],gr["ctrl"]],gr["ref"],"U",gr.get("alerts",[]))
    CARD_END()

    # ── Ceftriaxone ──────────────────────────────────────────────────────
    CARD("Ceftriaxone IV — Urgence infectieuse","")
    cr2,ce2=ceftriaxone(poids, age, atcd)
    if ce2: AL(ce2,"danger")
    else:
        for al_m,al_c in cr2.get("alerts",[]): AL(al_m,al_c)
        RX("Ceftriaxone IV",f"{cr2['dose_g']} g",
           [cr2["admin"],cr2["note"]],cr2["ref"],"U",cr2.get("alerts",[]))
    CARD_END()

    # ── Litican ──────────────────────────────────────────────────────────
    CARD("Litican IM — Antispasmodique (Protocole Hainaut)","")
    lr,le=litican(poids, age, atcd)
    if le: AL(le,"danger")
    else:
        for al_m,al_c in lr.get("alerts",[]): AL(al_m,al_c)
        RX("Litican IM (Tiémonium)",f"{lr['dose_mg']:.0f} mg",
           [lr["voie"],lr["dose_note"],lr["freq"]],lr["ref"],"2",lr.get("alerts",[]))
    CARD_END()

    # ── Salbutamol ────────────────────────────────────────────────────────
    CARD("Salbutamol nébulisation — Bronchospasme","")
    grav=st.select_slider("Gravité",["legere","moderee","severe"],"moderee",key="ph_grav",
        format_func=lambda x:{"legere":"Légère","moderee":"Modérée","severe":"Sévère"}[x])
    sr,se=salbutamol(poids, age, grav, atcd)
    if se: AL(se,"warning")
    else:
        for al_m,al_c in sr.get("alerts",[]): AL(al_m,al_c)
        RX("Salbutamol (Ventolin) nébulisation",f"{sr['dose_mg']} mg",
           [sr["admin"],sr["dilution"],sr["debit_o2"],sr["rep"]],sr["ref"],"2",sr.get("alerts",[]))
    CARD_END()

    # ── Furosémide ────────────────────────────────────────────────────────
    CARD("Furosémide IV — OAP cardiogénique","")
    fr2,fe=furosemide(poids, age, atcd)
    if fe: AL(fe,"danger")
    else:
        for al_m,al_c in fr2.get("alerts",[]): AL(al_m,al_c)
        RX("Furosémide IV (Lasix)",f"{fr2['dose_min']:.0f}-{fr2['dose_max']:.0f} mg",
           [fr2["admin"]],fr2["ref"],"2",fr2.get("alerts",[]))
    CARD_END()

    # ── Sepsis Bundle ─────────────────────────────────────────────────────
    CARD("Sepsis Bundle — Première heure (SSC 2021)","")
    sb_lact=st.number_input("Lactate (mmol/l — 0 si non dosé)",0.0,20.0,0.0,0.1,key="sb_l")
    sb=sepsis_bundle_1h(SS.v_pas or 120, sb_lact if sb_lact>0 else None,
                         SS.v_temp or 37, SS.v_fc or 80, poids, atcd)
    if sb["choc_septique"]: AL("CHOC SEPTIQUE — Réanimation immédiate","danger")
    for al_m,al_c in sb.get("alerts",[]): AL(al_m,al_c)
    for lbl,detail,css in sb["checklist"]:
        H(f'<div class="al {css}" style="padding:7px 14px;margin:3px 0;font-size:.78rem;">'
          f'<input type="checkbox" style="margin-right:8px;">'
          f'<strong>{lbl}</strong> — {detail}</div>')
    CARD_END()

    # ── Crise HTA ─────────────────────────────────────────────────────────
    CARD("Crise hypertensive — Cible adaptée à l'étiologie","")
    AL("Cibles DIFFÉRENTES selon l'étiologie — Ne jamais baisser trop vite","warning")
    motif_hta=st.selectbox("Contexte clinique",[
        "Urgence hypertensive standard","AVC ischémique (non thrombolysé)",
        "AVC ischémique (si thrombolyse)","AVC hémorragique",
        "Dissection aortique","OAP hypertensif",
    ], key="ph_hta")
    ch=crise_hypertensive(SS.v_pas or 120, motif_hta, poids, atcd)
    AL(f"Objectif : {ch['objectif']}",ch["priorite"])
    if ch.get("ci_labetalol"): AL("BPCO/Asthme — Labétalol CI — Nicardipine ou Urapidil","warning")
    RX(ch["med1"]["nom"]+" — 1er choix",ch["med1"]["dose"],[],ch["ref"],"U")
    RX(ch["med2"]["nom"]+" — Alternative",ch["med2"]["dose"],[],ch["ref"],"2")
    CARD_END()

    # ── Neutralisation AOD ────────────────────────────────────────────────
    CARD("Neutralisation AOD / AVK — Urgence hémorragique","")
    aod_mol=st.selectbox("Anticoagulant",[
        "Dabigatran (Pradaxa®)","Rivaroxaban (Xarelto®)","Apixaban (Eliquis®)",
        "Edoxaban (Lixiana®)","Acenocoumarol (Sintrom® / AVK)","Warfarine (Coumadine® / AVK)","Inconnu",
    ],key="ph_aod")
    aod_r=neutralisation_aod(aod_mol,"Hémorragie majeure",poids,atcd)
    ant=aod_r["antidote"]
    AL(aod_r["mesure_avant"],"warning")
    RX(ant["nom"],ant.get("delai",""),
       [ant["dose"],ant.get("dispo","")],ant["ref"],"3")
    CARD_END()

    # ── Kétamine IN pédiatrique ───────────────────────────────────────────
    if age < 18:
        CARD("Kétamine intranasale — Analgésie pédiatrique avant VVP","")
        kt_r,kt_e=ketamine_intranasale(poids, age, atcd)
        if kt_e: AL(kt_e,"danger")
        else:
            for al_m,al_c in kt_r.get("alerts",[]): AL(al_m,al_c)
            RX("Kétamine IN (Ketalar)",f"{kt_r['dose_mg']} mg",
               [kt_r["admin"],kt_r["onset"],kt_r["duree"],kt_r["surv"]],kt_r["ref"],"2",
               kt_r.get("alerts",[]))
        CARD_END()

    DISC()

# ═══════════════════════════════════════════════════════════════════════════════
# ONGLETS 7-9 — Réévaluation, Historique, SBAR
# ═══════════════════════════════════════════════════════════════════════════════
with T[6]:
    CARD("Réévaluation clinique","")
    if not SS.uid_cur:
        AL("Enregistrer d'abord un patient dans l'onglet Triage","info")
    else:
        st.caption(f"Patient actif : {SS.uid_cur}")
        rc1,rc2,rc3=st.columns(3)
        re_temp=rc1.number_input("T°",30.0,45.0,float(SS.v_temp),0.1,key="re_t")
        re_fc  =rc1.number_input("FC",20,220,int(SS.v_fc),key="re_fc")
        re_pas =rc2.number_input("PAS",40,260,int(SS.v_pas),key="re_pas")
        re_spo2=rc2.number_input("SpO2",50,100,int(SS.v_spo2),key="re_sp")
        re_fr  =rc3.number_input("FR",5,60,int(SS.v_fr),key="re_fr")
        re_gcs =rc3.number_input("GCS",3,15,int(SS.v_gcs),key="re_gcs")
        re_n2,_=calculer_news2(re_fr,re_spo2,o2,re_temp,re_pas,re_fc,re_gcs,SS.v_bpco)
        re_niv,re_just,_=french_triage(
            SS.motif,SS.det,re_fc,re_pas,re_spo2,re_fr,re_gcs,re_temp,age,re_n2,SS.gl)
        st.metric("NEWS2 réévaluation",re_n2,delta=re_n2-SS.v_news2,delta_color="inverse")
        TRI_CARD_INLINE(re_niv,re_just,re_n2)
        if re_n2>SS.v_news2: AL("NEWS2 en hausse — Réévaluation médicale urgente","danger")
        elif re_n2<SS.v_news2: AL("NEWS2 en baisse — Amélioration clinique","success")

        # Réévaluation douleur — obligation légale Belgique 2014
        if SS.t_reev:
            mins=(datetime.now()-SS.t_reev).total_seconds()/60
            if 25<=mins<=35:
                AL("⏱ Réévaluation douleur à 30 min POST-ANTALGIE — Obligatoire (Circulaire 2014)","warning")
            elif 55<=mins<=65:
                AL("⏱ Réévaluation douleur à 60 min POST-ANTALGIE — Obligatoire","warning")
            # Timer délai médecin selon niveau de triage
            delai_cible = {"M":5,"1":5,"2":15,"3A":30,"3B":60}.get(SS.niv, 60)
            if mins > delai_cible:
                AL(f"⏱ Délai cible Tri {SS.niv} dépassé ({delai_cible} min) — Relancer le médecin","danger")

        if st.button("✅ Enregistrer la réévaluation",use_container_width=True):
            SS.reevs.append({
                "h":datetime.now().strftime("%H:%M"),"fc":re_fc,"pas":re_pas,
                "spo2":re_spo2,"fr":re_fr,"gcs":re_gcs,"temp":re_temp,
                "n2":re_n2,"niv":re_niv,
            })
            st.success(f"Réévaluation à {SS.reevs[-1]['h']} — Tri {re_niv}")
    CARD_END()

    # ── Courbe temporelle vitaux ───────────────────────────────────────────
    if SS.reevs:
        COURBE_VITAUX(SS.reevs)

    # ── Checklist 5B avant injection ──────────────────────────────────────
    st.divider()
    CARD("Sécurité avant injection — Règle des 5B", "")
    st.caption("AR 78 sur l'exercice infirmier — AFMPS 2019 — Obligatoire avant toute injection")
    para_5b, _ = paracetamol(poids, age, atcd)
    nap_5b, _ = naproxene(poids, age, atcd)
    trad_5b, _ = tramadol(poids, age, atcd)
    dip_5b, _ = piritramide(poids, age, atcd)
    morph_5b, _ = morphine(poids, age, atcd)
    ves_5b, _ = vesiera(poids, age, atcd)
    gluc_5b, _ = glucose(poids, SS.gl, atcd) if SS.gl is not None else (None, None)
    eme_5b = protocole_epilepsie_ped(
        poids, age, float(SS.det.get("duree_min", 0) or 0),
        bool(SS.det.get("en_cours", False)), atcd, SS.gl,
    )
    med_sel = st.selectbox("Médicament à injecter", [
        "Perfu — Paracétamol IV",
        "Naproxène PO",
        "Tradonal® — Tramadol",
        "Dipidolor® — Piritramide",
        "Morphine IV titrée",
        "Litican IM (40 mg)",
        "Adrénaline IM (0,5 mg)",
        "Ceftriaxone IV (2 g)",
        "Glucose 30 % IV",
        "Salbutamol nébulisation",
        "Furosémide IV",
        "Midazolam buccal",
        "Vesiera® — Kétamine perfusion",
        "Acide tranexamique IV (1 g)",
        "Autre",
    ], key="re_5b_med")
    doses_default = {
        "Perfu — Paracétamol IV": f"{para_5b['dose_g']} g IV en 15 min" if para_5b else "1 g IV en 15 min",
        "Naproxène PO": f"{nap_5b['dose_mg']:.0f} mg PO" if nap_5b else "500 mg PO",
        "Tradonal® — Tramadol": f"{trad_5b['dose_mg']:.0f} mg PO" if trad_5b else "50 mg PO",
        "Dipidolor® — Piritramide": f"{dip_5b['dose_min']:.1f}-{dip_5b['dose_max']:.1f} mg IV lent" if dip_5b else "3-6 mg IV lent",
        "Morphine IV titrée": f"{morph_5b['dose_min']:.1f}-{morph_5b['dose_max']:.1f} mg IV lent" if morph_5b else "2-7,5 mg IV titré",
        "Litican IM (40 mg)": f"40 mg IM",
        "Adrénaline IM (0,5 mg)": "0,5 mg IM cuisse",
        "Ceftriaxone IV (2 g)": "2 g IV en 3-5 min",
        "Glucose 30 % IV": str(gluc_5b["vol"]) if gluc_5b else "Selon glycémie mesurée",
        "Salbutamol nébulisation": "2,5-5 mg nébulisation",
        "Furosémide IV": "40-80 mg IV lent",
        "Midazolam buccal": str(eme_5b["midazolam_buccal"]["dose"]),
        "Vesiera® — Kétamine perfusion": str(ves_5b["dose"]) if ves_5b else "Selon protocole algologue",
        "Acide tranexamique IV (1 g)": "1 g IV en 10 min",
        "Autre": "À compléter",
    }
    dose_pre = st.text_input("Dose calculée", value=doses_default.get(med_sel,""), key="re_5b_dose")
    voie_pre = st.selectbox("Voie", ["IV","IM","SC","IN (intranasale)","Buccale","Nébulisation","PO"], key="re_5b_voie")
    CHECKLIST_5B(
        medicament=med_sel,
        dose=dose_pre,
        voie=voie_pre,
        poids=st.session_state.get("p_kg", 70),
        uid=SS.uid_cur or SS.sid,
    )
    CARD_END()
    DISC()

with T[7]:
    reg=charger_registre()
    if reg:
        CARD("Statistiques session","")
        s1,s2,s3=st.columns(3)
        s1.metric("Patients",len(reg))
        s2.metric("Critiques (Tri 1/2)",sum(1 for r in reg if r.get("niv") in ("M","1","2")))
        s3.metric("NEWS2 moyen",round(sum(r.get("n2",0) for r in reg)/len(reg),1) if reg else 0)
        CARD_END()
    CARD("Registre session (RGPD — anonyme)","")
    if not reg: st.info("Aucun patient enregistré")
    else:
        for r in reg[:20]:
            c=st.columns([1,3,1,1])
            c[0].caption(r.get("heure","")[-5:]); c[1].write(r.get("motif",""))
            c[2].write(f"**Tri {r.get('niv','')}**"); c[3].caption(r.get("uid",""))
    CARD_END()
    CARD("Export RGPD","")
    if reg:
        out=io.StringIO(); w=csv_mod.writer(out)
        w.writerow(["uid","heure","motif","niv","n2","fc","pas","spo2","fr","temp","gcs","op"])
        for r in reg:
            w.writerow([r.get(k,"") for k in ["uid","heure","motif","niv","n2","fc","pas","spo2","fr","temp","gcs","op"]])
        st.download_button("📥 Télécharger CSV",data=out.getvalue(),
            file_name=f"akir_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",use_container_width=True)
    if st.button("🔐 Vérifier intégrité audit",use_container_width=True):
        ok,rapport=audit_verifier_integrite()
        AL(rapport,"success" if ok else "danger")
    CARD_END()
    DISC()

with T[8]:
    CARD("Transmission SBAR","")
    if not SS.niv:
        AL("Calculer d'abord le triage (onglet Triage ou Tri Rapide)","info")
    else:
        sbar=build_sbar(age,SS.motif,SS.cat,atcd,alg,o2,
                        SS.v_temp,SS.v_fc,SS.v_pas,SS.v_spo2,SS.v_fr,SS.v_gcs,
                        SS.eva,SS.v_news2,SS.niv,SS.just,SS.crit,SS.op or "IAO",SS.gl)
        SBAR_RENDER(sbar)
        txt=(f"RAPPORT SBAR — AKIR-IAO v19.0\n{'='*50}\n"
             f"S — Opérateur : {SS.op or 'IAO'} | {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
             f"    Motif : {SS.motif} | Triage : Tri {SS.niv} — {SS.just}\n"
             f"B — Âge : {age} ans | ATCD : {', '.join(atcd) or 'Aucun'} | Alg : {alg or 'Aucune'}\n"
             f"A — FC {SS.v_fc} | PAS {SS.v_pas} | SpO2 {SS.v_spo2} % | FR {SS.v_fr} | T° {SS.v_temp} | GCS {SS.v_gcs}/15\n"
             f"    NEWS2 : {SS.v_news2} | Critère : {SS.crit}\n"
             f"R — Orientation : {SECTEURS.get(SS.niv,'—')} | Délai cible : {DELAIS.get(SS.niv,'—')} min\n"
             f"    Remarques : [À compléter]\n"
             f"{'─'*50}\n"
             f"AKIR-IAO v19.0 — Dév. Ismail Ibn-Daifa — FRENCH SFMU V1.1 — Hainaut\n"
             f"RGPD : UID {SS.uid_cur or '—'} — Aucun identifiant nominal\n")
        st.download_button("📋 Télécharger SBAR (.txt)",data=txt,
            file_name=f"SBAR_{datetime.now().strftime('%Y%m%d_%H%M')}_Tri{SS.niv}.txt",
            mime="text/plain",use_container_width=True)
    CARD_END()
    DISC()
