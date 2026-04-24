# streamlit_app.py — Point d'entrée Streamlit Cloud pour AKIR-IAO

import streamlit as st
import uuid
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION DE LA PAGE (DOIT ÊTRE LE PREMIER APPEL STREAMLIT)
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AKIR-IAO — Pro",
    page_icon="+",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS DES MODULES MÉTIER
# ═══════════════════════════════════════════════════════════════════════════
from config import *
from clinical.news2 import calculer_news2, n2_meta
from clinical.triage import french_triage, verifier_coherence
from clinical.french_v12 import (
    FRENCH_MOTS_CAT, FRENCH_MOTIFS_RAPIDES,
    get_protocol, get_criterion_options,
)
from clinical.scores import (
    calculer_gcs, calculer_qsofa, calculer_timi,
    evaluer_fast, calculer_algoplus, evaluer_cfs,
)
from clinical.vitaux import si, sipa, mgdl_mmol
from clinical.pharmaco import (
    paracetamol, ketorolac, tramadol, piritramide,
    morphine, naloxone, adrenaline, glucose, ceftriaxone,
    litican, protocole_eva, protocole_epilepsie_ped,
    salbutamol, furosemide, ondansetron,
    acide_tranexamique, methylprednisolone,
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

MOTS_CAT = FRENCH_MOTS_CAT
MOTIFS_RAPIDES = FRENCH_MOTIFS_RAPIDES

# ═══════════════════════════════════════════════════════════════════════════
# CSS HOSPITALIER
# ═══════════════════════════════════════════════════════════════════════════
st.markdown(f"<style>{load_css()}</style>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# ÉTAT DE LA SESSION
# ═══════════════════════════════════════════════════════════════════════════
_DEF = {
    "sid": lambda: str(uuid.uuid4())[:8].upper(),
    "op": "",
    "t_arr": None,
    "t_cont": None,
    "t_reev": None,
    "histo": [],
    "reevs": [],
    "uid_cur": None,
}
for k, v in _DEF.items():
    if k not in st.session_state:
        st.session_state[k] = v() if callable(v) else v

# ═══════════════════════════════════════════════════════════════════════════
# EN-TÊTE
# ═══════════════════════════════════════════════════════════════════════════
H(f"""
<div class="app-hdr">
  <div class="app-hdr-title">AKIR-IAO v18.0 — Pro Edition</div>
  <div class="app-hdr-sub">Aide au Triage Infirmier — Urgences — Hainaut, Wallonie, Belgique</div>
  <div class="app-hdr-tags">
    <span class="tag">FRENCH SFMU V1.2</span>
    <span class="tag">BCFI Belgique</span>
    <span class="tag">RGPD</span>
    <span class="tag">Dév. : Ismail Ibn-Daifa</span>
  </div>
</div>
""")

# ═══════════════════════════════════════════════════════════════════════════
# BARRE LATÉRALE
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    SEC("Opérateur IAO")
    op_in = st.text_input("Code opérateur", value=st.session_state.op,
                          max_chars=10, placeholder="IAO01")
    if op_in:
        st.session_state.op = op_in.upper()

    SEC("Chronomètre")
    sa, sb = st.columns(2)
    if sa.button("Arrivée", use_container_width=True):
        st.session_state.t_arr = datetime.now()
        st.session_state.histo = []
        st.session_state.reevs = []
    if sb.button("Contact", use_container_width=True):
        st.session_state.t_cont = datetime.now()
    if st.session_state.t_arr:
        el = (datetime.now() - st.session_state.t_arr).total_seconds()
        m, s_ = divmod(int(el), 60)
        col = "#EF4444" if el > 600 else ("#F59E0B" if el > 300 else "#22C55E")
        H(f'<div style="text-align:center;font-family:\'JetBrains Mono\',monospace;'
          f'font-size:2.2rem;font-weight:700;color:{col};">{m:02d}:{s_:02d}</div>')

    SEC("Patient")
    age = st.number_input("Âge (ans)", 0, 120, 45, key="p_age")
    if age == 0:
        am = st.number_input("Âge en mois", 0, 11, 3, key="p_am")
        age = round(am / 12.0, 4)
        AL(f"Nourrisson {am} mois — seuils pédiatriques", "info")
    poids = st.number_input("Poids (kg)", 1, 250, 70, key="p_kg")
    atcd = st.multiselect("Antécédents pertinents", ATCD, key="p_atcd")
    alg = st.text_input("Allergies", key="p_alg", placeholder="ex: Pénicilline")
    o2 = st.checkbox("O₂ supplémentaire", key="p_o2")

    SEC("Session RGPD")
    st.caption(f"Session : {st.session_state.sid}")
    if st.button("Nouvelle session", use_container_width=True):
        for k, v in _DEF.items():
            st.session_state[k] = v() if callable(v) else v
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ONGLETS
# ═══════════════════════════════════════════════════════════════════════════
T = st.tabs(["Tri Rapide","Vitaux & GCS","Anamnèse","Triage",
             "Scores Cliniques","Pharmacie","Réévaluation",
             "Historique","Transmission SBAR"])

# Variables partagées (valeurs par défaut)
temp = 37.0; fr = 16; fc = 80; pas = 120; spo2 = 98; gcs = 15
news2 = 0; motif = ""; cat = ""; details = {}; eva = 0
niv = ""; just = ""; crit = ""; gl_global = None; bpco_g = False

# ═══════════════════════════════════════════════════════════════════════════
# ONGLET 1 — TRI RAPIDE
# ═══════════════════════════════════════════════════════════════════════════
with T[0]:
    CARD("Constantes vitales", "+")
    c1,c2,c3 = st.columns(3)
    temp = c1.number_input("Température (°C)", 30.0,45.0,37.0,0.1, key="r_t")
    fc = c2.number_input("FC (bpm)", 20,220,80, key="r_fc")
    pas = c3.number_input("PAS (mmHg)", 40,260,120, key="r_pas")
    c4,c5,c6 = st.columns(3)
    spo2 = c4.number_input("SpO2 (%)", 50,100,98, key="r_sp")
    fr = c5.number_input("FR (/min)", 5,60,16, key="r_fr")
    gcs = c6.number_input("GCS (3–15)", 3,15,15, key="r_gcs")
    CARD_END()

    CARD("Motif & Sécurité", "+")
    bpco_r = st.checkbox("Patient BPCO connu ?", key="r_bp")
    if bpco_r: AL("BPCO — Cible SpO2 : 88–92 % — Échelle 2 NEWS2 activée", "warning")
    news2,nw = calculer_news2(fr,spo2,o2,temp,pas,fc,gcs,bpco_r)
    for w in nw: AL(w,"warning")
    GAUGE(news2,bpco_r)
    motif = st.selectbox("Motif de recours", MOTIFS_RAPIDES, key="r_mot")
    cat = "Tri rapide"
    eva = int(st.select_slider("EVA",[str(i) for i in range(11)],value="0",key="r_eva"))
    details = {"eva":eva,"atcd":atcd}
    details["purpura"] = st.checkbox("Purpura non effaçable (test du verre)", key="r_pur")
    if details.get("purpura"): PURPURA(details)
    gl_r = GLYC_WIDGET("r_gl","Glycémie capillaire (mg/dl)")
    if gl_r: details["glycemie_mgdl"]=gl_r; gl_global=gl_r
    CARD_END()

    if st.button("Calculer le niveau de triage", type="primary", use_container_width=True):
        N2_BANNER(news2); PURPURA(details)
        nv,jt,cr = french_triage(motif,details,fc,pas,spo2,fr,gcs,temp,age,news2,gl_r)
        niv,just,crit = nv,jt,cr
        TRI_CARD_INLINE(nv,jt,news2)
        D,A = verifier_coherence(fc,pas,spo2,fr,gcs,temp,eva,motif,atcd,details,news2,gl_r)
        for d in D: AL(d,"danger")
        for a in A: AL(a,"warning")
    VITAUX(fc,pas,spo2,fr,temp,gcs,bpco_r)

# ═══════════════════════════════════════════════════════════════════════════
# ONGLET 2 — VITAUX & GCS
# ═══════════════════════════════════════════════════════════════════════════
with T[1]:
    CARD("Paramètres vitaux", "+")
    v1,v2,v3 = st.columns(3)
    temp = v1.number_input("Température (°C)", 30.0,45.0,37.0,0.1, key="v_t")
    fc = v1.number_input("FC (bpm)", 20,220,80, key="v_fc")
    pas = v2.number_input("PAS (mmHg)", 40,260,120, key="v_pas")
    spo2 = v2.number_input("SpO2 (%)", 50,100,98, key="v_sp")
    fr = v3.number_input("FR (/min)", 5,60,16, key="v_fr")
    CARD_END()

    CARD("Glasgow Coma Scale", "+")
    g1,g2,g3 = st.columns(3)
    gy = g1.selectbox("Yeux (Y)", [4,3,2,1],
                      format_func=lambda x: {4:"4 — Spontanée",3:"3 — À la demande",
                                             2:"2 — À la douleur",1:"1 — Aucune"}[x], key="v_gy")
    gv = g2.selectbox("Verbale (V)", [5,4,3,2,1],
                      format_func=lambda x: {5:"5 — Orientée",4:"4 — Confuse",
                                             3:"3 — Mots",2:"2 — Sons",1:"1 — Aucune"}[x], key="v_gv")
    gm = g3.selectbox("Motrice (M)", [6,5,4,3,2,1],
                      format_func=lambda x: {6:"6 — Obéit aux ordres",5:"5 — Localise",
                                             4:"4 — Évitement",3:"3 — Flexion anormale",
                                             2:"2 — Extension",1:"1 — Aucune"}[x], key="v_gm")
    gcs,_ = calculer_gcs(gy,gv,gm)
    st.metric("Score GCS", f"{gcs} / 15")
    CARD_END()

    bpco_v = "BPCO" in atcd
    news2,nw = calculer_news2(fr,spo2,o2,temp,pas,fc,gcs,bpco_v)
    for w in nw: AL(w,"warning")
    bpco_g = bpco_v
    GAUGE(news2,bpco_v)
    VITAUX(fc,pas,spo2,fr,temp,gcs,bpco_v)
    N2_BANNER(news2)
    c1,c2 = st.columns(2)
    with c1:
        sh = si(fc,pas); css_si = "si-c" if sh>=1.0 else ("si-w" if sh>=0.8 else "si-ok")
        lbl_si = "CHOC PROBABLE" if sh>=1.0 else ("Surveillance rapprochée" if sh>=0.8 else "Normal")
        H(f'<div class="si-box"><div class="si-l">Shock Index</div><div class="si-v {css_si}">{sh}</div><div class="si-l">{lbl_si}</div></div>')
    with c2:
        if age<18:
            sv,si_i,si_a = sipa(fc,age)
            css_sipa = "si-c" if si_a else "si-ok"
            H(f'<div class="si-box"><div class="si-l">SIPA Pédiatrique</div><div class="si-v {css_sipa}">{sv}</div><div class="si-l" style="font-size:.6rem;">{si_i}</div></div>')
    DISC()

# ═══════════════════════════════════════════════════════════════════════════
# ONGLET 3 — ANAMNÈSE (abrégé pour test — tu peux compléter ensuite)
# ═══════════════════════════════════════════════════════════════════════════
with T[2]:
    CARD("Évaluation de la douleur", "+")
    eva = int(st.select_slider("EVA (0=aucune — 10=maximale)",
                               [str(i) for i in range(11)], value="0", key="a_eva"))
    CARD_END()

    CARD("Motif de recours", "+")
    cat = st.selectbox("Catégorie", list(MOTS_CAT.keys()), key="a_cat")
    motif = st.selectbox("Motif principal", MOTS_CAT[cat], key="a_mot")
    CARD_END()

    st.info("Les autres champs d'anamnèse seront ajoutés ici (questions discriminantes FRENCH).")

# ═══════════════════════════════════════════════════════════════════════════
# ONGLET 4 — TRIAGE (simplifié)
# ═══════════════════════════════════════════════════════════════════════════
with T[3]:
    if not motif: motif = "Fievre"; cat = "Infectio"
    bpco_t = "BPCO" in atcd or details.get("bpco",False)
    news2,nw = calculer_news2(fr,spo2,o2,temp,pas,fc,gcs,bpco_t)
    for w in nw: AL(w,"warning")
    if not details.get("glycemie_mgdl") and not gl_global:
        glt = GLYC_WIDGET("t_gl","Glycémie capillaire (mg/dl)")
        if glt: details["glycemie_mgdl"]=glt; gl_global=glt
    gl_t = details.get("glycemie_mgdl") or gl_global

    proto = get_protocol(motif)
    if proto:
        CARD("Referentiel FRENCH v1.2", "+")
        st.caption(f"{proto['category']} | Niveau par defaut : Tri {proto['default']}")
        opts = get_criterion_options(motif)
        idx = st.selectbox(
            "Critere discriminant",
            range(len(opts)),
            format_func=lambda i: opts[i]["label"],
            key=f"t_french_criterion_{proto['id'][:80]}",
        )
        if idx:
            details["french_level"] = opts[idx]["level"]
            details["french_criterion"] = opts[idx]["text"]
        else:
            details.pop("french_level", None)
            details.pop("french_criterion", None)
        CARD_END()

    niv,just,crit = french_triage(motif,details,fc,pas,spo2,fr,gcs,temp,age,news2,gl_t)
    N2_BANNER(news2); PURPURA(details)
    GAUGE(news2,bpco_t)
    TRI_CARD_INLINE(niv,just,news2)
    st.caption(f"Critère : {crit}")
    if st.button("Enregistrer ce patient", type="primary", use_container_width=True):
        uid = enregistrer_patient({"motif":motif,"cat":cat,"niv":niv,"n2":news2,
                                   "fc":fc,"pas":pas,"spo2":spo2,"fr":fr,
                                   "temp":temp,"gcs":gcs,"op":st.session_state.op})
        st.session_state.uid_cur = uid
        st.session_state.reevs = []
        st.session_state.t_reev = datetime.now()
        st.session_state.histo.insert(0,{"uid":uid,"h":datetime.now().strftime("%H:%M"),
                                          "motif":motif,"niv":niv,"n2":news2})
        st.success(f"Patient enregistré — UID : {uid}")
    TRI_BANNER_FIXED(niv,just,news2)
    DISC()

# ═══════════════════════════════════════════════════════════════════════════
# ONGLET 5 — SCORES CLINIQUES (simplifié)
# ═══════════════════════════════════════════════════════════════════════════
with T[4]:
    CARD("qSOFA", "+")
    qs,qp,qw = calculer_qsofa(fr or 16, gcs or 15, pas or 120)
    for w in qw: AL(w,"warning")
    st.metric("qSOFA", f"{qs}/3")
    CARD_END()

    CARD("FAST — AVC", "+")
    f1,f2,f3,f4 = st.columns(4)
    ff = f1.checkbox("Face", key="sf"); fa = f2.checkbox("Bras", key="sa")
    fs = f3.checkbox("Langage", key="ss"); ft = f4.checkbox("Début brutal", key="st2")
    fsc,fi,fal = evaluer_fast(ff,fa,fs,ft)
    AL(fi, "danger" if fal else ("warning" if fsc>=1 else "success"))
    CARD_END()

    CARD("TIMI", "+")
    tsc,_ = calculer_timi(age, 0, False, False, False, False, 0)
    st.metric("TIMI", f"{tsc}/7")
    CARD_END()
    DISC()

# ═══════════════════════════════════════════════════════════════════════════
# ONGLET 6 — PHARMACIE (exemple paracétamol)
# ═══════════════════════════════════════════════════════════════════════════
with T[5]:
    CARD("Paracétamol IV", "+")
    r,e = paracetamol(poids)
    if e: AL(e,"danger")
    else:
        H(f"Dose : {r['dose_g']} g — {r['vol']} — {r['freq']}")
    CARD_END()
    DISC()

# ═══════════════════════════════════════════════════════════════════════════
# ONGLETS 7-8-9 : placeholders
# ═══════════════════════════════════════════════════════════════════════════
with T[6]: st.info("Réévaluation — à implémenter")
with T[7]: st.info("Historique — à implémenter")
with T[8]: st.info("Transmission SBAR — à implémenter")

# ═══════════════════════════════════════════════════════════════════════════
# DISCLAIMER
# ═══════════════════════════════════════════════════════════════════════════
DISC()
