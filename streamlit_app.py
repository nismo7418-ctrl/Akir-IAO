# streamlit_app.py — AKIR-IAO v19.0 — Système Expert Grade Hospitalier
# Développeur : Ismail Ibn-Daifa — Hainaut, Wallonie, Belgique
# Architecture : Modulaire — FRENCH SFMU V1.1 — BCFI — RGPD

import streamlit as st
import uuid, io, csv as csv_mod, traceback
from datetime import datetime

# ── Configuration page (DOIT être le premier appel Streamlit) ─────────────────
st.set_page_config(
    page_title="AKIR-IAO v19.0",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded",
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
    taradyl_im, diclofenac_im,
    clevidipine, meopa, midazolam_iv,
)
from clinical.french_v12 import (
    FRENCH_MOTS_CAT, FRENCH_MOTIFS_RAPIDES,
    get_protocol, render_discriminants, apply_discriminant_selection,
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

# ── Session State — initialisation des clés nécessaires ──────────────────────
SS = st.session_state
_defaults = {
    "op": "", "sid": str(uuid.uuid4())[:8].upper(),
    "uid": None,
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
}
for _k, _v in _defaults.items():
    if _k not in SS:
        SS[_k] = _v

if not SS.get("uid"):
    SS.uid = SS.sid

load_css()


def _show_news2(fr, spo2, o2_flag, temp, pas, fc, gcs, bpco) -> None:
    SS.v_news2, nw = calculer_news2(fr, spo2, o2_flag, temp, pas, fc, gcs, bpco)
    for w in nw:
        AL(w, "danger" if "IMMÉDIAT" in w or "ENGAGEMENT" in w else "warning")


def WK(base: str, scope: str | None = None) -> str:
    parts = [str(SS.get("uid") or SS.get("sid") or "session")]
    if scope:
        parts.append(str(scope))
    parts.append(str(base))
    return "__".join(p.replace(" ", "_") for p in parts if p)


def _ensure_sidebar_state() -> None:
    widget_defaults = {
        "p_age": int(SS.get("age") or 45),
        "p_am": int(SS.get("age_mois") or 3),
        "p_kg": int(SS.get("poids") or 70),
        "p_taille": int(SS.get("taille") or 170),
        "p_alg": SS.get("alg") or "",
        "p_atcd_other": list(SS.get("atcd_other") or []),
        WK("p_o2"): bool(SS.get("o2", False)),
        WK("r_eva"): str(int(SS.get("eva") or 0)),
    }
    for key, value in widget_defaults.items():
        if key not in SS:
            SS[key] = value


# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATION PRINCIPALE — Wrapper de sécurité
# ═══════════════════════════════════════════════════════════════════════════════
try:
    H("""
    <div class="app-hdr">
      <div class="app-hdr-title">AKIR-IAO v19.0 — Système expert de triage</div>
      <div class="app-hdr-sub">Outil professionnel d'aide à la décision clinique — Urgences — Hainaut, Wallonie</div>
      <div class="app-hdr-tags">
        <span class="tag">FRENCH SFMU V1.1</span>
        <span class="tag">BCFI Belgique</span>
        <span class="tag">RGPD</span>
        <span class="tag">Développeur : Ismail Ibn-Daifa</span>
      </div>
    </div>
    """)

    _ensure_sidebar_state()

    # ═══════════════════════════════════════════════════════════════════════════
    # SIDEBAR — Profil patient + Opérateur
    # ═══════════════════════════════════════════════════════════════════════════
    with st.sidebar:
        SEC("Identification opérateur")
        op_in = st.text_input("Code opérateur", value=SS.op, max_chars=10,
                               placeholder="IAO01", help="Identifiant unique pour cette session")
        if op_in:
            SS.op = op_in.upper()
        st.caption("Utiliser un identifiant court et local pour cette session.")

        SEC("Chronomètre")
        ca, cb = st.columns(2)
        if ca.button("⏱ Arrivée", key=WK("timer_arrivee"), use_container_width=True):
            SS.t_arr = datetime.now()
            SS.histo = []
            SS.reevs = []
        if cb.button("👨‍⚕️ 1er contact", key=WK("timer_contact"), use_container_width=True):
            SS.t_cont = datetime.now()
        if SS.t_arr:
            el = (datetime.now() - SS.t_arr).total_seconds()
            m_, s_ = divmod(int(el), 60)
            col = "#EF4444" if el > 600 else ("#F59E0B" if el > 300 else "#22C55E")
            H(f'<div style="text-align:center;font-family:monospace;font-size:2rem;'
              f'font-weight:700;color:{col};">{m_:02d}:{s_:02d}</div>')

        SEC("Patient")
        age = st.number_input("Âge (ans)", 0, 120, int(SS.age or 45), key="p_age")
        if age == 0:
            am  = st.number_input("Âge en mois", 0, 11, int(SS.age_mois or 3), key="p_am")
            SS.age_mois = am
            age = round(am / 12.0, 4)
            AL(f"Nourrisson {am} mois — Seuils pédiatriques actifs", "info")
        else:
            SS.age_mois = 0
        SS.age = age

        poids  = st.number_input("Poids (kg)", 1, 250, int(SS.poids or 70), key="p_kg")
        taille = st.number_input("Taille (cm)", 50, 220, int(SS.taille or 170), key="p_taille")
        SS.poids = poids
        SS.taille = taille

        if taille > 0 and age >= 18:
            imc = round(poids / (taille / 100) ** 2, 1)
            if   imc < 18.5: AL(f"IMC {imc} — Insuffisance pondérale", "warning")
            elif imc < 25.0: st.caption(f"IMC {imc} — Normal")
            elif imc < 30.0: AL(f"IMC {imc} — Surpoids", "info")
            elif imc < 40.0: AL(f"IMC {imc} — Obésité", "warning")
            else:             AL(f"IMC {imc} — Obésité morbide ≥ 40 — Adapter doses opioïdes", "danger")

        # ── Antécédents ──────────────────────────────────────────────────────
        with st.expander("📋 Antécédents (ATCD)", expanded=False):
            sb_a1, sb_a2 = st.columns(2)
            atcd_checks = {
                "HTA":                            sb_a1.checkbox("HTA",            key=WK("sb_hta")),
                "Insuffisance cardiaque":         sb_a2.checkbox("Insuff. card.",   key=WK("sb_ic")),
                "Coronaropathie / SCA antérieur": sb_a1.checkbox("Coronaropathie", key=WK("sb_coro")),
                "AVC / AIT antérieur":            sb_a2.checkbox("AVC / AIT",      key=WK("sb_avc")),
                "BPCO":                           sb_a1.checkbox("BPCO",           key=WK("sb_bpco")),
                "Asthme":                         sb_a2.checkbox("Asthme",         key=WK("sb_asthme")),
                "Diabète type 2":                 sb_a1.checkbox("Diabète T2",     key=WK("sb_diab2")),
                "Diabète type 1":                 sb_a2.checkbox("Diabète T1",     key=WK("sb_diab1")),
                "Insuffisance rénale chronique":  sb_a1.checkbox("Insuff. rénale", key=WK("sb_ir")),
                "Insuffisance hépatique":         sb_a2.checkbox("Insuff. hépa.",  key=WK("sb_ih")),
                "Épilepsie":                      sb_a1.checkbox("Épilepsie",      key=WK("sb_epi")),
                "Fibrillation atriale":           sb_a2.checkbox("FA",             key=WK("sb_fa")),
                "Drépanocytose":                  sb_a1.checkbox("Drépanocytose",  key=WK("sb_drep")),
                "Immunodépression":               sb_a2.checkbox("Immunodépression", key=WK("sb_immuno")),
            }

        # ── Facteurs favorisants ──────────────────────────────────────────────
        with st.expander("⚠️ Facteurs favorisants", expanded=False):
            sb_f1, sb_f2 = st.columns(2)
            risk_checks = {
                "Grossesse":                    sb_f1.checkbox("Grossesse",       key=WK("sb_gros")),
                "Allaitement":                  sb_f2.checkbox("Allaitement",     key=WK("sb_allait")),
                "Obésité morbide (IMC ≥ 40)":  sb_f1.checkbox("Obésité IMC≥40", key=WK("sb_ob")),
                "Chirurgie récente (<4 sem.)":  sb_f2.checkbox("Chir. récente",   key=WK("sb_chir")),
                "Tabagisme":                    sb_f1.checkbox("Tabagisme",       key=WK("sb_tabac")),
            }
            if risk_checks.get("Grossesse"):
                trimestre = st.selectbox("Trimestre",
                    ["T1 (< 14 SA)", "T2 (14-28 SA)", "T3 (> 28 SA)"], key="sb_trim")
                AL(f"Grossesse {trimestre} — Adapter les thérapeutiques", "warning")

        # ── Traitements en cours ─────────────────────────────────────────────
        with st.expander("💊 Traitements en cours", expanded=False):
            sb_t1, sb_t2 = st.columns(2)
            trt_checks = {
                "Anticoagulants/AOD":           sb_t1.checkbox("Anticoagulants", key=WK("sb_acg")),
                "Antiagrégants plaquettaires":  sb_t2.checkbox("Antiagrégants",  key=WK("sb_aap")),
                "Bêta-bloquants":               sb_t1.checkbox("Bêtabloquants",  key=WK("sb_beta")),
                "Corticoïdes au long cours":    sb_t2.checkbox("Corticoïdes",    key=WK("sb_cort")),
                "IMAO (inhibiteurs MAO)":       sb_t1.checkbox("IMAO",           key=WK("sb_imao")),
                "Chimiothérapie en cours":      sb_t2.checkbox("Chimio",         key=WK("sb_chimo")),
            }

        # Liste ATCD consolidée
        _all_checks = {**atcd_checks, **risk_checks, **trt_checks}
        _base_atcd  = [lbl for lbl, chk in _all_checks.items() if chk]
        other_atcd  = st.multiselect(
            "Autres antécédents", [a for a in ATCD if a not in _base_atcd], key="p_atcd_other"
        )
        SS.atcd_other = other_atcd
        atcd = _base_atcd + other_atcd

        alg = st.text_input("Allergies connues", key="p_alg", placeholder="ex: Pénicilline")
        SS.alg = alg
        o2  = st.checkbox("O₂ supplémentaire", key=WK("p_o2"))
        SS.o2 = o2

        # ── Pharmacovigilance ────────────────────────────────────────────────
        with st.expander("🚨 Alertes Pharmacovigilance", expanded=True):
            if trt_checks.get("IMAO (inhibiteurs MAO)"):
                AL("IMAO — Tramadol contre-indiqué", "danger")
            if atcd_checks.get("Immunodépression") or trt_checks.get("Chimiothérapie en cours"):
                AL("Immunodéprimé — Seuil fébrile abaissé à 38.3 °C", "warning")
            if atcd_checks.get("Drépanocytose"):
                AL("Drépanocytose — Morphine titrée précoce si EVA ≥ 6", "warning")
            if trt_checks.get("Anticoagulants/AOD"):
                AL("Anticoagulants — Tout traumatisme = Tri 2 minimum", "warning")
            if atcd_checks.get("Insuffisance rénale chronique"):
                AL("Insuff. rénale — AINS contre-indiqués", "danger")
            if risk_checks.get("Grossesse"):
                AL("Grossesse — AINS déconseillés au T3, morphine avec prudence", "warning")
            if trt_checks.get("Bêta-bloquants"):
                AL("Bêtabloquants — FC masquée, tachycardie relative", "warning")

    # ═══════════════════════════════════════════════════════════════════════════
    # ONGLETS PRINCIPAUX
    # ═══════════════════════════════════════════════════════════════════════════
    T = st.tabs(["📊 Évaluation & Triage", "🧬 Scores Cliniques",
                 "💊 Pharmacopée Adaptative", "📋 Synthèse"])

    # ───────────────────────────────────────────────────────────────────────────
    # ONGLET 0 — ÉVALUATION & TRIAGE
    # ───────────────────────────────────────────────────────────────────────────
    with T[0]:
        ET = st.tabs(["Triage Rapide", "Paramètres Vitaux", "Anamnèse", "Triage Complet"])

        # ── Sous-onglet 0.0 : Triage Rapide ──────────────────────────────────
        with ET[0]:
            CARD("Constantes vitales", "")
            c1, c2, c3 = st.columns(3)
            SS.v_temp = c1.number_input("Température (°C)", 30.0, 45.0,
                                         float(SS.v_temp), 0.1, key="r_t")
            SS.v_fc   = c2.number_input("FC (bpm)",   20, 220, int(SS.v_fc),   key="r_fc")
            SS.v_pas  = c3.number_input("PAS (mmHg)", 40, 260, int(SS.v_pas),  key="r_pas")
            c4, c5, c6 = st.columns(3)
            SS.v_spo2 = c4.number_input("SpO2 (%)",   50, 100, int(SS.v_spo2), key="r_sp")
            SS.v_fr   = c5.number_input("FR (/min)",   5,  60, int(SS.v_fr),   key="r_fr")
            SS.v_gcs  = c6.number_input("GCS (3-15)",  3,  15, int(SS.v_gcs),  key="r_gcs")
            CARD_END()

            CARD("Motif & Sécurité", "")
            SS.v_bpco = st.checkbox("Patient BPCO connu ?", key=WK("r_bp"),
                                     value=bool("BPCO" in atcd))
            if SS.v_bpco:
                BPCO_WIDGET(True)

            st.info("Saisir les constantes et le motif, puis appuyer sur Calculer le triage.")
            _show_news2(SS.v_fr, SS.v_spo2, o2, SS.v_temp, SS.v_pas,
                        SS.v_fc, SS.v_gcs, SS.v_bpco)
            GAUGE(SS.v_news2, SS.v_bpco)

            SS.motif = st.selectbox("Motif de recours", MOTIFS_RAPIDES, key="r_mot")
            rapid_eva_key = WK("r_eva")
            if rapid_eva_key not in SS:
                SS[rapid_eva_key] = str(SS.eva)
            SS.eva = int(st.select_slider("EVA", [str(i) for i in range(11)],
                                           key=rapid_eva_key))
            EVA_BAR(SS.eva)
            det = {"eva": SS.eva, "atcd": atcd}

            # ── Drapeaux rouges dans un formulaire (pas de rechargement à chaque clic)
            with st.form("form_red_flags"):
                det["purpura"] = st.checkbox("Purpura non effaçable (test du verre)",
                                              key=WK("r_pur"))
                gl_r = GLYC_WIDGET("r_gl", "Glycémie capillaire (mg/dl)")
                st.form_submit_button("Valider les drapeaux rouges",
                                       use_container_width=True)

            if det.get("purpura"):
                PURPURA(det)
            if gl_r:
                det["glycemie_mgdl"] = gl_r
                SS.gl = gl_r

            N2_BANNER(SS.v_news2)
            CARD_END()

            if st.button("⚡ Calculer le triage", type="primary",
                          key=WK("triage_rapide_calc"),
                          use_container_width=True):
                SS.niv, SS.just, SS.crit = french_triage(
                    SS.motif, det, SS.v_fc, SS.v_pas, SS.v_spo2,
                    SS.v_fr, SS.v_gcs, SS.v_temp, age, SS.v_news2, SS.gl,
                )
                SS.det = det
                TRI_CARD_INLINE(SS.niv, SS.just, SS.v_news2)
                D, A = verifier_coherence(
                    SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr,
                    SS.v_gcs, SS.v_temp, SS.eva, SS.motif,
                    atcd, det, SS.v_news2, SS.gl)
                for d in D: AL(d, "danger")
                for a in A: AL(a, "warning")

            VITAUX(SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr, SS.v_temp, SS.v_gcs, SS.v_bpco)
            DISC()

        # ── Sous-onglet 0.1 : Paramètres Vitaux ──────────────────────────────
        with ET[1]:
            CARD("Paramètres vitaux détaillés", "")
            v1, v2, v3 = st.columns(3)
            SS.v_temp = v1.number_input("Température (°C)", 30.0, 45.0,
                                         float(SS.v_temp), 0.1, key="v_t2")
            SS.v_fc   = v2.number_input("FC (bpm)",   20, 220, int(SS.v_fc),   key="v_fc2")
            SS.v_pas  = v3.number_input("PAS (mmHg)", 40, 260, int(SS.v_pas),  key="v_pas2")
            v4, v5, v6 = st.columns(3)
            SS.v_spo2 = v4.number_input("SpO2 (%)",   50, 100, int(SS.v_spo2), key="v_sp2")
            SS.v_fr   = v5.number_input("FR (/min)",   5,  60, int(SS.v_fr),   key="v_fr2")
            SS.v_gcs  = v6.number_input("GCS (3-15)",  3,  15, int(SS.v_gcs),  key="v_gcs2")
            SS.v_bpco = st.checkbox("Patient BPCO", key=WK("v_bp2"),
                                     value=bool(SS.v_bpco or ("BPCO" in atcd)))
            CARD_END()

            CARD("GCS Détaillé", "")
            gcs_y = st.select_slider("Ouverture des yeux", [1, 2, 3, 4], 4, key=WK("gcs_y"),
                format_func=lambda x: {1:"1–Absente",2:"2–Douleur",
                                        3:"3–Bruit",4:"4–Spontanée"}[x])
            gcs_v = st.select_slider("Réponse verbale", [1, 2, 3, 4, 5], 5, key=WK("gcs_v"),
                format_func=lambda x: {1:"1–Aucune",2:"2–Sons",3:"3–Mots",
                                        4:"4–Confus",5:"5–Orientée"}[x])
            gcs_m = st.select_slider("Réponse motrice", [1, 2, 3, 4, 5, 6], 6, key=WK("gcs_m"),
                format_func=lambda x: {1:"1–Aucune",2:"2–Extension",3:"3–Flex. anorm.",
                                        4:"4–Retrait",5:"5–Localise",6:"6–Obéit"}[x])
            gcs_res  = calculer_gcs(gcs_y, gcs_v, gcs_m, age)
            SS.v_gcs = gcs_res.get("score_val") or 15
            AL(gcs_res.get("interpretation",""),
               "danger"  if (gcs_res.get("score_val") or 15) <= 8  else
               "warning" if (gcs_res.get("score_val") or 15) <= 12 else "success")
            AL(gcs_res.get("recommendation",""), "info")
            CARD_END()

            _show_news2(SS.v_fr, SS.v_spo2, o2, SS.v_temp, SS.v_pas,
                        SS.v_fc, SS.v_gcs, SS.v_bpco)
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

        # ── Sous-onglet 0.2 : Anamnèse ────────────────────────────────────────
        with ET[2]:
            non_comm = ("Démence" in atcd or (age >= 75 and SS.v_gcs < 15))
            eva_result = EVA_WIDGET_COMPLET(key_prefix="ana", age=age,
                                             non_communicant=non_comm)
            SS.eva = eva_result.get("eva", 0)
            SS.det.update({
                "eva": SS.eva,
                "pqrst": eva_result.get("pqrst", {}),
                "atcd": atcd,
            })

            CARD("Motif de recours", "")
            SS.cat   = st.selectbox("Catégorie", list(MOTS_CAT.keys()), key="a_cat")
            SS.motif = st.selectbox("Motif principal", MOTS_CAT[SS.cat],  key="a_mot")
            CARD_END()

            if "Brûlure" in SS.motif or "brulure" in SS.motif.lower():
                brul = SCHEMA_BRULURES(poids=poids, age=age)
                SS.det.update({
                    "surface_pct": brul.get("surface_pct"),
                    "baux": brul.get("baux"),
                    "profondeur": brul.get("profondeur"),
                })

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

        # ── Sous-onglet 0.3 : Triage Complet ─────────────────────────────────
        with ET[3]:
            if not SS.motif:
                SS.motif = "Fièvre"
                SS.cat   = "Infectieux"

            _show_news2(SS.v_fr, SS.v_spo2, o2, SS.v_temp, SS.v_pas,
                        SS.v_fc, SS.v_gcs, SS.v_bpco)

            det = SS.det if isinstance(SS.det, dict) else {}
            det["atcd"] = atcd
            if not det.get("glycemie_mgdl") and not SS.gl:
                gl_t = GLYC_WIDGET("t_gl", "Glycémie capillaire (mg/dl)")
                if gl_t:
                    det["glycemie_mgdl"] = gl_t
                    SS.gl  = gl_t
                    SS.det = det
            gl_t = det.get("glycemie_mgdl") or SS.gl

            SS.niv, SS.just, SS.crit = french_triage(
                SS.motif, det, SS.v_fc, SS.v_pas, SS.v_spo2,
                SS.v_fr, SS.v_gcs, SS.v_temp, age, SS.v_news2, gl_t,
            )
            proto = get_protocol(SS.motif)
            if proto and proto.get("criteria"):
                CARD("Critères discriminants FRENCH", "")
                selected_crit = render_discriminants(SS.motif, key=WK("t_disc"))
                CARD_END()
                SS.niv, SS.just, SS.crit = apply_discriminant_selection(
                    SS.niv, SS.just, SS.crit, selected_crit
                )
            N2_BANNER(SS.v_news2)
            PURPURA(det)
            GAUGE(SS.v_news2, SS.v_bpco)
            TRI_CARD_INLINE(SS.niv, SS.just, SS.v_news2)
            st.caption(f"Critère FRENCH : {SS.crit}")

            D, A = verifier_coherence(
                SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr,
                SS.v_gcs, SS.v_temp, SS.eva, SS.motif,
                atcd, det, SS.v_news2, gl_t)
            for d in D: AL(d, "danger")
            for a in A: AL(a, "warning")

            if st.button("💾 Enregistrer ce patient", type="primary",
                          key=WK("save_patient"),
                          use_container_width=True):
                uid = enregistrer_patient({
                    "motif": SS.motif, "cat": SS.cat, "niv": SS.niv,
                    "n2": SS.v_news2, "fc": SS.v_fc, "pas": SS.v_pas,
                    "spo2": SS.v_spo2, "fr": SS.v_fr, "temp": SS.v_temp,
                    "gcs": SS.v_gcs, "op": SS.op,
                })
                SS.uid_cur = uid
                SS.reevs   = []
                SS.t_reev  = datetime.now()
                SS.histo.insert(0, {
                    "uid": uid, "h": datetime.now().strftime("%H:%M"),
                    "motif": SS.motif, "niv": SS.niv, "n2": SS.v_news2,
                })
                st.success(f"✅ Patient enregistré — UID : {uid}")

            if SS.niv:
                st.divider()
                CARD("📋 Synthèse IAO — Copier pour le dossier", "")
                _si_val = round((SS.v_fc or 80) / max(1, (SS.v_pas or 120)), 2)
                _gl_txt  = (f"{SS.gl:.0f} mg/dl ({SS.gl/18.016:.1f} mmol/l)"
                            if SS.gl else "Non mesurée")
                _atcd_txt = ", ".join(atcd) if atcd else "Aucun antécédent connu"
                _alg_txt  = alg if alg else "Aucune allergie connue"
                _now_txt  = datetime.now().strftime("%d/%m/%Y à %H:%M")

                _synthese_txt = f"""SYNTHÈSE IAO — {_now_txt}
Opérateur : {SS.op or "IAO"} | Session anonyme : {SS.uid_cur or "—"}
{"═"*55}
NIVEAU DE TRIAGE : {SS.niv} — {LABELS.get(SS.niv, "")}
Justification    : {SS.just}
Référence FRENCH : {SS.crit}
Orientation      : {SECTEURS.get(SS.niv,"—")} | Délai médecin ≤ {DELAIS.get(SS.niv,"?")} min
{"─"*55}
MOTIF DE RECOURS : {SS.motif} ({SS.cat})
EVA / Douleur    : {SS.eva}/10
{"─"*55}
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
{"─"*55}
ANTÉCÉDENTS      : {_atcd_txt}
ALLERGIES        : {_alg_txt}
O₂ supplémentaire : {"OUI" if o2 else "Non"}
{"═"*55}
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

    # ───────────────────────────────────────────────────────────────────────────
    # ONGLET 1 — SCORES CLINIQUES
    # ───────────────────────────────────────────────────────────────────────────
    with T[1]:
        S = st.tabs(["Cardio / Neuro", "Infectio / Respiratoire", "Règles Imagerie"])

        with S[0]:
            s_l, s_r = st.columns(2)

            with s_l:
                CARD("qSOFA — Dépistage Sepsis", "")
                st.caption("Seymour CW et al., JAMA 2016")
                qs = calculer_qsofa(SS.v_fr or 16, SS.v_gcs or 15, SS.v_pas or 120)
                sv = qs.get("score_val") or 0
                AL(qs.get("interpretation",""),
                   "danger" if sv >= 2 else "warning" if sv == 1 else "success")
                AL(qs.get("recommendation",""), "info")
                CARD_END()

                CARD("Score HEART — Douleur thoracique", "")
                st.caption("Six AJ et al., NHJ 2008")
                h1, h2 = st.columns(2)
                h_hist = h1.select_slider("Histoire", [0,1,2], key=WK("ht_h"),
                    format_func=lambda x: {0:"0–Peu évocateur",1:"1–Modéré",2:"2–Très suspect"}[x])
                h_ecg  = h2.select_slider("ECG",     [0,1,2], key=WK("ht_e"),
                    format_func=lambda x: {0:"0–Normal",1:"1–Non spéc.",2:"2–Bloc/STEMI"}[x])
                h_age  = h1.select_slider("Âge",     [0,1,2], key=WK("ht_a"),
                    format_func=lambda x: {0:"0–<45 ans",1:"1–45-65",2:"2–>65 ans"}[x])
                h_rfcv = h2.select_slider("FRCV",    [0,1,2], key=WK("ht_r"),
                    format_func=lambda x: {0:"0–Aucun",1:"1–1-2",2:"2–≥3 ou ATCD"}[x])
                h_trop = h1.select_slider("Troponine",[0,1,2], key=WK("ht_t"),
                    format_func=lambda x: {0:"0–Normale",1:"1–1-3x N",2:"2–>3x N"}[x])
                ht = calculer_heart(h_hist, h_ecg, h_age, h_rfcv, h_trop)
                AL(ht.get("interpretation",""),
                   "danger"  if (ht.get("score_val") or 0) >= 7 else
                   "warning" if (ht.get("score_val") or 0) >= 4 else "success")
                AL(ht.get("recommendation",""), "info")
                CARD_END()

                # TIMI — visible uniquement si motif = douleur thoracique
                _motif_lc = (SS.motif or "").lower()
                _is_thoracique = any(k in _motif_lc
                    for k in ("thoracique","sca","coronaire","infarctus"))
                if _is_thoracique:
                    CARD("Score TIMI — UA/NSTEMI (contexte SCA)", "")
                    st.caption("Antman EM et al., JAMA 2000")
                    st.info("ℹ️ TIMI activé automatiquement — motif : douleur thoracique")
                    ti1, ti2 = st.columns(2)
                    ti_age  = ti1.checkbox("Âge ≥ 65 ans",              key=WK("ti_age"),  value=age >= 65)
                    ti_frcv = ti2.checkbox("≥ 3 facteurs de risque CV",  key=WK("ti_frcv"))
                    ti_sten = ti1.checkbox("Sténose coronaire ≥ 50 %",   key=WK("ti_sten"))
                    ti_ecg  = ti2.checkbox("Déviation ST à l'ECG",        key=WK("ti_ecg"))
                    ti_ang  = ti1.checkbox("≥ 2 épisodes angineux/24 h", key=WK("ti_ang"))
                    ti_asp  = ti2.checkbox("Aspirine dans les 7 jours",   key=WK("ti_asp"))
                    ti_trop = ti1.checkbox("Marqueurs cardiaques +",      key=WK("ti_trop"))
                    ti_res   = calculer_timi(ti_age, ti_frcv, ti_sten, ti_ecg,
                                             ti_ang, ti_asp, ti_trop)
                    ti_score = ti_res.get("score_val") or 0
                    H(f"""<div style="background:#1E293B;border-radius:10px;padding:14px;
                        margin:10px 0;text-align:center;">
                      <div style="font-size:.65rem;color:#64748B;text-transform:uppercase;">Score TIMI</div>
                      <div style="font-size:2.5rem;font-weight:900;color:{'#EF4444' if ti_score>=5 else '#F59E0B' if ti_score>=3 else '#22C55E'};">
                        {ti_score}/7</div>
                      <div style="font-size:.75rem;color:#94A3B8;margin-top:4px;">
                        {ti_res.get("interpretation","")}</div>
                    </div>""")
                    AL(ti_res.get("recommendation",""),
                       "danger" if ti_score >= 5 else
                       "warning" if ti_score >= 3 else "info")
                    CARD_END()
                else:
                    H('<div style="background:#F1F5F9;border-radius:10px;padding:12px;'
                      'text-align:center;color:#94A3B8;font-size:.75rem;margin:8px 0;">'
                      'TIMI NSTEMI — Disponible uniquement si motif = Douleur thoracique / SCA</div>')

            with s_r:
                CARD("BE-FAST — Dépistage AVC", "")
                st.caption("Kothari RU, Ann Emerg Med 1999")
                f1, f2 = st.columns(2)
                bf_ba  = f1.checkbox("Balance (équilibre)", key=WK("bf_b"))
                bf_ey  = f2.checkbox("Eyes (vision)",       key=WK("bf_e"))
                bf_fa  = f1.checkbox("Face (asymétrie)",    key=WK("bf_f"))
                bf_ar  = f2.checkbox("Arm (déficit moteur)",key=WK("bf_a"))
                bf_sp  = f1.checkbox("Speech (langage)",    key=WK("bf_sp"))
                bf_ti  = f2.text_input("Heure dernière fois vu bien", key="bf_t",
                                        placeholder="14:30")
                bf_res = evaluer_fast(bf_fa, bf_ar, bf_sp, bf_ti, bf_ba, bf_ey)
                AL(bf_res.get("interpretation",""),
                   "danger" if (bf_res.get("score_val") or 0) >= 1 else "success")
                AL(bf_res.get("recommendation",""), "info")
                CARD_END()

                CARD("Algoplus — Douleur non communicant", "")
                st.caption("Rat P et al., Eur J Pain 2011")
                a1, a2 = st.columns(2)
                alg_v = a1.checkbox("Visage douloureux",     key=WK("alg_v"))
                alg_r = a2.checkbox("Regard distant",        key=WK("alg_r"))
                alg_p = a1.checkbox("Plaintes verbales",     key=WK("alg_p"))
                alg_a = a2.checkbox("Attitudes défensives",  key=WK("alg_a"))
                alg_c = a1.checkbox("Comportements inhabituels", key=WK("alg_c"))
                alg_res = calculer_algoplus(alg_v, alg_r, alg_p, alg_a, alg_c)
                AL(alg_res.get("interpretation",""),
                   "danger" if (alg_res.get("score_val") or 0) >= 2 else "success")
                AL(alg_res.get("recommendation",""), "info")
                CARD_END()

        with S[1]:
            s2_l, s2_r = st.columns(2)

            with s2_l:
                CARD("CURB-65 — Pneumonie communautaire", "")
                st.caption("Lim WS et al., Thorax 2003")
                cb_c = st.checkbox("Confusion",              key=WK("cb_c"))
                cb_u = st.checkbox("Urée > 7 mmol/l",       key=WK("cb_u"))
                cb_r = st.checkbox("FR ≥ 30/min",           key=WK("cb_r"),
                                    value=(SS.v_fr or 16) >= 30)
                cb_b = st.checkbox("PAS < 90 ou PAD < 60",  key=WK("cb_b"),
                                    value=(SS.v_pas or 120) < 90)
                cb_a = st.checkbox("Âge ≥ 65 ans",          key=WK("cb_a"),
                                    value=age >= 65)
                cb_res = calculer_curb65(cb_c, cb_u, cb_r, cb_b, cb_a)
                AL(cb_res.get("interpretation",""),
                   "danger"  if (cb_res.get("score_val") or 0) >= 3 else
                   "warning" if (cb_res.get("score_val") or 0) == 2 else "success")
                AL(cb_res.get("recommendation",""), "info")
                CARD_END()

                CARD("Wells TVP", "")
                st.caption("Wells PS et al., Lancet 1997")
                wt1, wt2 = st.columns(2)
                wt_ca = wt1.checkbox("Cancer actif",          key=WK("wt_ca"))
                wt_im = wt2.checkbox("Immobilisation > 3 j",  key=WK("wt_im"))
                wt_ch = wt1.checkbox("Chirurgie récente",     key=WK("wt_ch"))
                wt_se = wt2.checkbox("Sensibilité veine",     key=WK("wt_se"))
                wt_oe = wt1.checkbox("Œdème à godet",        key=WK("wt_oe"))
                wt_am = wt2.checkbox("Asymétrie mollet",      key=WK("wt_am"))
                wt_av = wt1.checkbox("Asymétrie membre",      key=WK("wt_av"))
                wt_vc = wt2.checkbox("Veines collatérales",   key=WK("wt_vc"))
                wt_an = wt1.checkbox("ATCD TVP",              key=WK("wt_an"))
                wt_da = wt2.checkbox("Diag. alternatif prob.",key=WK("wt_da"))
                wt_res = calculer_wells_tvp(wt_ca, wt_im, wt_ch, wt_se, wt_oe,
                                             wt_am, wt_av, wt_vc, wt_an, wt_da)
                AL(wt_res.get("interpretation",""),
                   "danger"  if (wt_res.get("score_val") or 0) >= 3 else
                   "warning" if (wt_res.get("score_val") or 0) >= 1 else "success")
                AL(wt_res.get("recommendation",""), "info")
                CARD_END()

            with s2_r:
                CARD("Wells EP", "")
                st.caption("Wells PS et al., Thromb Haemost 2000")
                we1, we2 = st.columns(2)
                we_tvp = we1.checkbox("Symptômes TVP",         key=WK("we_tvp"))
                we_ep  = we2.checkbox("EP plus probable",      key=WK("we_ep"))
                we_fc  = we1.checkbox("FC > 100/min",          key=WK("we_fc"),
                                       value=(SS.v_fc or 80) > 100)
                we_im  = we2.checkbox("Immobilisation/chir.",  key=WK("we_im"))
                we_an  = we1.checkbox("ATCD TVP/EP",           key=WK("we_an"))
                we_he  = we2.checkbox("Hémoptysie",            key=WK("we_he"))
                we_ca  = we1.checkbox("Cancer",                key=WK("we_ca"))
                we_res = calculer_wells_ep(we_tvp, we_ep, we_fc, we_im,
                                            we_an, we_he, we_ca)
                AL(we_res.get("interpretation",""),
                   "danger"  if (we_res.get("score_val") or 0) > 4 else
                   "warning" if (we_res.get("score_val") or 0) > 1 else "success")
                AL(we_res.get("recommendation",""), "info")
                CARD_END()

                CARD("CFS — Clinical Frailty Scale", "")
                st.caption("Rockwood K et al., CMAJ 2005")
                cfs_n = st.select_slider("Niveau fragilité", list(range(1, 10)), 1,
                    key=WK("cfs_n"),
                    format_func=lambda x: {
                        1:"1–Très robuste",2:"2–Bien portant",3:"3–Maladies traitées",
                        4:"4–Vulnérable",5:"5–Légèrement fragile",6:"6–Modérément fragile",
                        7:"7–Sévèrement fragile",8:"8–Très sévèrement",9:"9–Phase terminale",
                    }[x])
                cfs_res = evaluer_cfs(cfs_n)
                AL(cfs_res.get("interpretation",""),
                   "danger" if cfs_n >= 7 else "warning" if cfs_n >= 5 else "success")
                AL(cfs_res.get("recommendation",""), "info")
                CARD_END()

        with S[2]:
            s3_l, s3_r = st.columns(2)

            with s3_l:
                CARD("Règles d'Ottawa — Cheville / Pied", "")
                st.caption("Stiell IG et al., JAMA 1993")
                ot_ap = st.checkbox("Incapacité d'appui (4 pas)", key=WK("ot_ap"))
                ot1, ot2 = st.columns(2)
                ot_mm = ot1.checkbox("Douleur malléole médiale",   key=WK("ot_mm"))
                ot_tl = ot2.checkbox("Douleur malléole latérale",  key=WK("ot_tl"))
                ot_5m = ot1.checkbox("Douleur base 5e métatarse",  key=WK("ot_5m"))
                ot_nv = ot2.checkbox("Douleur naviculaire",        key=WK("ot_nv"))
                ot_res = regle_ottawa_cheville(ot_mm, ot_tl, ot_5m, ot_nv, ot_ap)
                AL(ot_res.get("interpretation",""),
                   "warning" if (ot_res.get("score_val") or 0) else "success")
                AL(ot_res.get("recommendation",""), "info")
                CARD_END()

            with s3_r:
                CARD("Règle Canadienne — TDM cérébral (GCS 13-15)", "")
                st.caption("Stiell IG et al., Lancet 2001")
                AL("Non applicable si : GCS < 13 | coagulopathie | convulsion | < 16 ans",
                   "warning")
                cc1, cc2 = st.columns(2)
                cc_g  = cc1.checkbox("GCS < 15 à 2 h",          key=WK("cc_g"))
                cc_s  = cc2.checkbox("Suspicion fracture ouverte",key=WK("cc_s"))
                cc_f  = cc1.checkbox("Signe fracture base crâne",key=WK("cc_f"))
                cc_v  = cc2.checkbox("Vomissements ≥ 2",        key=WK("cc_v"))
                cc_a  = cc1.checkbox("Âge ≥ 65 ans",            key=WK("cc_a"),
                                      value=age >= 65)
                cc_am = cc2.checkbox("Amnésie ≥ 30 min",        key=WK("cc_am"))
                cc_m  = cc1.checkbox("Mécanisme dangereux",      key=WK("cc_m"))
                cc_res = regle_canadian_ct(cc_g, cc_s, cc_f, cc_v, cc_a, cc_am, cc_m)
                AL(cc_res.get("interpretation",""),
                   "danger"  if (cc_res.get("score_val") or 0) == 2 else
                   "warning" if (cc_res.get("score_val") or 0) == 1 else "success")
                AL(cc_res.get("recommendation",""), "info")
                CARD_END()

        DISC()

    # ───────────────────────────────────────────────────────────────────────────
    # ONGLET 2 — PHARMACOPÉE ADAPTATIVE
    # ───────────────────────────────────────────────────────────────────────────
    with T[2]:
        gl_ph = (SS.det.get("glycemie_mgdl") if isinstance(SS.det, dict) else None) or SS.gl
        _dose_mode = "mg/kg" if age < 15 else "adulte"

        H(f"""<div style="background:linear-gradient(135deg,#004A99,#0066CC);
            color:#fff;border-radius:10px;padding:12px 18px;margin-bottom:12px;
            display:flex;justify-content:space-between;align-items:center;">
          <div>
            <div style="font-size:.7rem;opacity:.8;">Doses calculées pour</div>
            <div style="font-size:1.4rem;font-weight:800;">{poids} kg — {age} ans
              <span style="font-size:.8rem;opacity:.7;margin-left:8px;">({_dose_mode})</span>
            </div>
          </div>
          <div style="font-size:.72rem;opacity:.8;text-align:right;">
            ATCD : {len(atcd)} | Allergies : {alg or 'aucune'}
          </div>
        </div>""")

        # ── Intelligence clinique : Tri → Pharma ─────────────────────────────
        _tri_critique = SS.niv in ("M", "1", "2")
        _eva_severe   = SS.eva >= 7
        _is_asthme    = "Asthme" in atcd

        if _tri_critique and _eva_severe:
            H(f"""<div class="pharma-urgent">
              ⚠️ TRI {SS.niv} — EVA {SS.eva}/10 — ANTALGIE MAJEURE PRIORITAIRE<br>
              <span style="font-size:.76rem;font-weight:400;opacity:.9;">
                Piritramide IV ou Morphine IV titrée à initier sans délai
                — Réévaluation EVA obligatoire à 30 min (Circulaire 2014)
              </span></div>""")

        # Alertes ATCD → Pharma contextuelles
        if "IMAO (inhibiteurs MAO)" in atcd:
            AL("IMAO — Tramadol contre-indiqué", "danger")
        if "Insuffisance cardiaque" in atcd:
            AL("Insuffisance cardiaque — Remplissage réduit à 15 ml/kg", "warning")
        if _is_asthme:
            AL("ASTHME — AINS déconseillés (risque bronchospasme) — Préférer paracétamol/opioïdes", "danger")
        if "HTA" in atcd:
            AL("HTA — Surveiller la TA sous AINS (naproxène, diclofénac, kétorolac)", "warning")
        if gl_ph is None:
            AL("Glycémie non saisie — Glucose 30 % désactivé", "warning")

        # ── Palier 1 ─────────────────────────────────────────────────────────
        CARD("Paracétamol IV — Palier 1", "")
        para_rx, para_err = paracetamol(poids, age, atcd)
        if para_err:
            AL(para_err, "danger")
        else:
            for m_, c_ in (para_rx or {}).get("alerts", []): AL(m_, c_)
            RX("Paracétamol IV (Perfalgan)",
               (para_rx or {}).get("dose_display",
                   f"{(para_rx or {}).get('dose_mg', 1000):.0f} mg"),
               [(para_rx or {}).get("admin",""), (para_rx or {}).get("note","")],
               (para_rx or {}).get("ref","BCFI"), "1",
               (para_rx or {}).get("alerts",[]))
        CARD_END()

        ph_c1, ph_c2 = st.columns(2)

        with ph_c1:
            CARD("Naproxène PO — AINS palier 1", "")
            nap_rx, nap_err = naproxene(poids, age, atcd)
            if nap_err:
                AL(nap_err, "warning")
            else:
                RX("Naproxène PO", f"{(nap_rx or {}).get('dose_mg', 500):.0f} mg",
                   [(nap_rx or {}).get("admin",""), (nap_rx or {}).get("note","")],
                   (nap_rx or {}).get("ref","BCFI"), "1")
            CARD_END()

            CARD("Taradyl® (Kétorolac) IM — AINS puissant", "")
            # Avertissement AINS si insuffisance rénale
            if "Insuffisance rénale chronique" in atcd:
                AL("AINS CONTRE-INDIQUÉ — Insuffisance rénale chronique", "danger")
            else:
                kt2_rx, kt2_err = ketorolac(poids, age, atcd)
                if kt2_err:
                    AL(f"🔒 {kt2_err}", "danger")
                else:
                    for m_, c_ in (kt2_rx or {}).get("alerts", []): AL(m_, c_)
                    RX("Taradyl® 30 mg/ml IM",
                       f"{(kt2_rx or {}).get('dose_mg', 30):.0f} mg",
                       [(kt2_rx or {}).get("admin",""), (kt2_rx or {}).get("note","")],
                       (kt2_rx or {}).get("ref","BCFI"), "1",
                       (kt2_rx or {}).get("alerts",[]))
            CARD_END()

            CARD("Voltarène® (Diclofénac) 75 mg IM — Adulte", "")
            # Avertissement AINS si insuffisance rénale
            if "Insuffisance rénale chronique" in atcd:
                AL("AINS CONTRE-INDIQUÉ — Insuffisance rénale chronique", "danger")
            else:
                dic_rx, dic_err = diclofenac(poids, age, atcd)
                if dic_err:
                    AL(f"🔒 {dic_err}", "danger")
                else:
                    for m_, c_ in (dic_rx or {}).get("alerts", []): AL(m_, c_)
                    RX("Voltarène® 75 mg/3 ml IM",
                       f"{(dic_rx or {}).get('dose_mg', 75):.0f} mg",
                       [(dic_rx or {}).get("admin",""), (dic_rx or {}).get("note","")],
                       (dic_rx or {}).get("ref","BCFI"), "1",
                       (dic_rx or {}).get("alerts",[]))
            CARD_END()

        with ph_c2:
            CARD("Tramadol — Palier 2", "")
            tram_rx, tram_err = tramadol(poids, age, atcd)
            if tram_err:
                AL(tram_err, "danger" if "contre" in tram_err.lower() else "warning")
            else:
                for m_, c_ in (tram_rx or {}).get("alerts", []): AL(m_, c_)
                RX("Tramadol (Tradonal)",
                   f"{(tram_rx or {}).get('dose_mg', 50):.0f} mg",
                   [(tram_rx or {}).get("admin",""), (tram_rx or {}).get("note","")],
                   (tram_rx or {}).get("ref","BCFI"), "2")
            CARD_END()

        CARD("Piritramide IV — Palier 3 (Dipidolor)", "")
        dip_rx, dip_err = piritramide(poids, age, atcd)
        if dip_err:
            AL(dip_err, "danger")
        else:
            for m_, c_ in (dip_rx or {}).get("alerts", []): AL(m_, c_)
            RX("Piritramide IV (Dipidolor)",
               f"{(dip_rx or {}).get('dose_min', 0):.1f}–{(dip_rx or {}).get('dose_max', 0):.1f} mg",
               [(dip_rx or {}).get("admin",""), (dip_rx or {}).get("note","")],
               (dip_rx or {}).get("ref","BCFI"), "3",
               (dip_rx or {}).get("alerts",[]))
        CARD_END()

        CARD("Morphine IV titrée — Palier 3", "")
        morph_rx, morph_err = morphine(poids, age, atcd)
        if morph_err:
            AL(morph_err, "danger")
        else:
            for m_, c_ in (morph_rx or {}).get("alerts", []): AL(m_, c_)
            RX("Morphine IV",
               f"{(morph_rx or {}).get('dose_min', 0):.1f}–{(morph_rx or {}).get('dose_max', 0):.1f} mg",
               [(morph_rx or {}).get("admin",""), (morph_rx or {}).get("note","")],
               (morph_rx or {}).get("ref","BCFI"), "3",
               (morph_rx or {}).get("alerts",[]))
        CARD_END()

        # ── Urgences vitales ──────────────────────────────────────────────────
        ph2_c1, ph2_c2 = st.columns(2)

        with ph2_c1:
            CARD("Adrénaline IM — Anaphylaxie", "")
            ar, ae = adrenaline(poids, atcd)
            if ae:
                AL(ae, "danger")
            else:
                for m_, c_ in (ar or {}).get("alerts", []): AL(m_, c_)
                RX("Adrénaline IM (Sterop 1 mg/ml)",
                   f"{(ar or {}).get('dose_mg', 0.5)} mg",
                   [(ar or {}).get("voie",""), (ar or {}).get("note",""),
                    (ar or {}).get("rep","")],
                   (ar or {}).get("ref","BCFI"), "U",
                   (ar or {}).get("alerts",[]))
            CARD_END()

        with ph2_c2:
            CARD("Naloxone IV — Antidote opioïdes", "")
            dep_ph = st.checkbox("Patient dépendant aux opioïdes", key=WK("ph_dep"))
            nr, _ = naloxone(poids, age, dep_ph, atcd)
            if nr:
                for m_, c_ in (nr or {}).get("alerts", []): AL(m_, c_)
                RX("Naloxone IV (Narcan)",
                   f"{(nr or {}).get('dose', 0.4)} mg",
                   [(nr or {}).get("admin",""), (nr or {}).get("note","")],
                   (nr or {}).get("ref","BCFI"), "U",
                   (nr or {}).get("alerts",[]))
            CARD_END()

        CARD("Glucose 30 % IV — Hypoglycémie", "")
        if gl_ph is None:
            RX_LOCK("Glycémie capillaire non saisie — Mesurer d'abord la glycémie")
        else:
            gr, ge = glucose(poids, gl_ph, atcd)
            if ge:
                AL(ge, "info")
            else:
                for m_, c_ in (gr or {}).get("alerts", []): AL(m_, c_)
                RX("Glucose 30 % IV",
                   f"{(gr or {}).get('dose_g', 0)} g",
                   [(gr or {}).get("vol",""), (gr or {}).get("ctrl","")],
                   (gr or {}).get("ref","BCFI"), "U",
                   (gr or {}).get("alerts",[]))
        CARD_END()

        CARD("Ceftriaxone IV — Urgence infectieuse", "")
        cr2, ce2 = ceftriaxone(poids, age, atcd)
        if ce2:
            AL(ce2, "danger")
        else:
            for m_, c_ in (cr2 or {}).get("alerts", []): AL(m_, c_)
            RX("Ceftriaxone IV",
               f"{(cr2 or {}).get('dose_g', 2)} g",
               [(cr2 or {}).get("admin",""), (cr2 or {}).get("note","")],
               (cr2 or {}).get("ref","BCFI"), "U",
               (cr2 or {}).get("alerts",[]))
        CARD_END()

        CARD("Litican IM — Antispasmodique (Protocole Hainaut)", "")
        lr, le = litican(poids, age, atcd)
        if le:
            AL(le, "danger")
        else:
            for m_, c_ in (lr or {}).get("alerts", []): AL(m_, c_)
            RX("Litican IM (Tiémonium)",
               f"{(lr or {}).get('dose_mg', 40):.0f} mg",
               [(lr or {}).get("voie",""), (lr or {}).get("dose_note",""),
                (lr or {}).get("freq","")],
               (lr or {}).get("ref","BCFI"), "2",
               (lr or {}).get("alerts",[]))
        CARD_END()

        CARD("Salbutamol nébulisation — Bronchospasme", "")
        grav = st.select_slider("Gravité", ["legere","moderee","severe"], "moderee",
            key=WK("ph_grav"),
            format_func=lambda x: {"legere":"Légère","moderee":"Modérée","severe":"Sévère"}[x])
        sr, se = salbutamol(poids, age, grav, atcd)
        if se:
            AL(se, "warning")
        else:
            RX("Salbutamol (Ventolin) nébulisation",
               f"{(sr or {}).get('dose_mg', 2.5)} mg",
               [(sr or {}).get("admin",""), (sr or {}).get("dilution",""),
                (sr or {}).get("debit_o2",""), (sr or {}).get("rep","")],
               (sr or {}).get("ref","BCFI"), "2")
        CARD_END()

        CARD("Sepsis Bundle — Première heure (SSC 2021)", "")
        sb_lact = st.number_input("Lactate (mmol/l — 0 si non dosé)",
                                   0.0, 20.0, 0.0, 0.1, key="sb_l")
        sb = sepsis_bundle_1h(SS.v_pas or 120,
                               sb_lact if sb_lact > 0 else None,
                               SS.v_temp or 37, SS.v_fc or 80, poids, atcd)
        _sb = sb or {}
        if _sb.get("choc_septique"):
            AL("CHOC SEPTIQUE — Réanimation immédiate", "danger")
        for m_, c_ in _sb.get("alerts", []): AL(m_, c_)
        for lbl, detail, css in _sb.get("checklist", []):
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
            AL(f"Objectif : {(_ch_payload or {}).get('cible','Cible clinique à confirmer')}",
               "warning")
            for m_, c_ in (_ch_payload or {}).get("alerts", []): AL(m_, c_)
        CARD_END()

        # ── Clévidipine IV (Vesierra®) — HTA réfractaire ─────────────────────
        CARD("Clévidipine IV (Vesierra®) — HTA sévère réfractaire", "")
        st.caption("BCFI / ESC 2023 — Inhibiteur calcique IV ultrarapide (T½ ~1 min)")
        clev_ctx = st.selectbox("Contexte HTA", [
            "HTA sévère", "OAP hypertensif", "Dissection aortique", "Péri-opératoire",
        ], key="ph_clev_ctx")
        clev_rx, clev_err = clevidipine(SS.v_pas or 120, poids, clev_ctx, atcd)
        if clev_err:
            AL(f"🔒 {clev_err}", "danger")
        else:
            for m_, c_ in (clev_rx or {}).get("alerts", []): AL(m_, c_)
            AL(f"Cible : {(clev_rx or {}).get('cible','—')}", "warning")
            RX("Clévidipine IV (Vesierra® 0,5 mg/ml)",
               f"{(clev_rx or {}).get('debit_init',1)} → max {(clev_rx or {}).get('debit_max',32)} mg/h",
               [(clev_rx or {}).get("admin",""),
                (clev_rx or {}).get("note","")],
               (clev_rx or {}).get("ref","BCFI"), "U",
               (clev_rx or {}).get("alerts",[]))
        CARD_END()

        # ── Midazolam IV — Sédation / Convulsion ────────────────────────────
        ph3_c1, ph3_c2 = st.columns(2)
        with ph3_c1:
            CARD("Midazolam IV (Hypnovel®) — Sédation/Convulsion", "")
            st.caption("BCFI — Benzodiazépine IV — Antidote : Flumazénil")
            midaz_ind = st.radio("Indication",
                ["sedation", "convulsion"], horizontal=True, key="ph_midaz_ind",
                format_func=lambda x: "Sédation procédurale" if x == "sedation" else "Crise convulsive")
            midaz_rx, midaz_err = midazolam_iv(poids, age, midaz_ind, atcd)
            if midaz_err:
                AL(f"🔒 {midaz_err}", "danger")
            else:
                for m_, c_ in (midaz_rx or {}).get("alerts", []): AL(m_, c_)
                RX("Midazolam IV (Hypnovel®)",
                   (midaz_rx or {}).get("dose_display", "—"),
                   [(midaz_rx or {}).get("admin",""),
                    (midaz_rx or {}).get("note",""),
                    (midaz_rx or {}).get("antidote","")],
                   (midaz_rx or {}).get("ref","BCFI"), "2",
                   (midaz_rx or {}).get("alerts",[]))
            CARD_END()

        # ── MEOPA (Kalinox®) — Analgésie procédurale ────────────────────────
        with ph3_c2:
            CARD("MEOPA (Kalinox® 50/50) — Analgésie procédurale", "")
            st.caption("BCFI / SFMU — 50 % O₂ / 50 % N₂O — Anxiolyse/Analgésie")
            meopa_rx, meopa_err = meopa(age, atcd)
            if meopa_err:
                AL(f"🔒 {meopa_err}", "danger")
            else:
                for m_, c_ in (meopa_rx or {}).get("alerts", []): AL(m_, c_)
                RX("MEOPA — Kalinox® 50/50",
                   (meopa_rx or {}).get("melange","50% O₂/N₂O"),
                   [(meopa_rx or {}).get("admin",""),
                    (meopa_rx or {}).get("note",""),
                    f"Débit : {(meopa_rx or {}).get('debit','')} — Durée max : {(meopa_rx or {}).get('duree_max','')}"],
                   (meopa_rx or {}).get("ref","BCFI"), "2",
                   (meopa_rx or {}).get("alerts",[]))
            CARD_END()

        if age < 18:
            CARD("Protocole anticonvulsivant pédiatrique", "")
            st.caption("BCFI / Lignes directrices belges — EME Pédiatrique")
            _det = SS.det if isinstance(SS.det, dict) else {}
            dur_epi  = float(_det.get("duree_min", 0) or 0)
            encours  = bool(_det.get("en_cours", False))
            eme = protocole_epilepsie_ped(poids, age, dur_epi, encours, atcd)
            _eme = eme or {}
            if _eme.get("eme_etabli"):
                AL(f"EME établi ({dur_epi:.0f} min) — Traitement 2e ligne requis", "danger")
            e1, e2 = st.columns(2)
            with e1:
                mid = _eme.get("midazolam_buccal") or {}
                RX("Midazolam buccal",   mid.get("dose","?"), [mid.get("note","")],
                   mid.get("ref","BCFI"), "2")
                diz = _eme.get("diazepam_rectal") or {}
                RX("Diazépam rectal",    diz.get("dose","?"), [diz.get("note","")],
                   diz.get("ref","BCFI"), "2")
            with e2:
                lor = _eme.get("lorazepam_iv") or {}
                RX("Lorazépam IV",       lor.get("dose","?"), [lor.get("note","")],
                   lor.get("ref","BCFI"), "2")
                if _eme.get("eme_etabli"):
                    lev = _eme.get("levetiracetam_iv") or {}
                    RX("Lévétiracétam IV", lev.get("dose","?"), [lev.get("note","")],
                       lev.get("ref","BCFI"), "3")
            CARD_END()

        DISC()

    # ───────────────────────────────────────────────────────────────────────────
    # ONGLET 3 — SYNTHÈSE
    # ───────────────────────────────────────────────────────────────────────────
    with T[3]:
        ST = st.tabs(["Réévaluation", "Historique", "Transmission SBAR"])

        with ST[0]:
            CARD("Réévaluation clinique", "")
            if not SS.uid_cur:
                AL("Enregistrer d'abord un patient dans l'onglet Triage", "info")
            else:
                st.caption(f"Patient actif : {SS.uid_cur}")
                rc1, rc2, rc3 = st.columns(3)
                re_temp = rc1.number_input("T°",   30.0, 45.0, float(SS.v_temp), 0.1, key="re_t")
                re_fc   = rc1.number_input("FC",    20, 220, int(SS.v_fc),   key="re_fc")
                re_pas  = rc2.number_input("PAS",   40, 260, int(SS.v_pas),  key="re_pas")
                re_spo2 = rc2.number_input("SpO2",  50, 100, int(SS.v_spo2), key="re_sp")
                re_fr   = rc3.number_input("FR",     5,  60, int(SS.v_fr),   key="re_fr")
                re_gcs  = rc3.number_input("GCS",    3,  15, int(SS.v_gcs),  key="re_gcs")
                re_n2, _ = calculer_news2(re_fr, re_spo2, o2, re_temp, re_pas,
                                           re_fc, re_gcs, SS.v_bpco)
                _det_reev = SS.det if isinstance(SS.det, dict) else {}
                re_niv, re_just, _ = french_triage(
                    SS.motif, _det_reev, re_fc, re_pas, re_spo2,
                    re_fr, re_gcs, re_temp, age, re_n2, SS.gl)
                st.metric("NEWS2 réévaluation", re_n2,
                           delta=re_n2 - SS.v_news2, delta_color="inverse")
                TRI_CARD_INLINE(re_niv, re_just, re_n2)
                if re_n2 > SS.v_news2:
                    AL("NEWS2 en hausse — Réévaluation médicale urgente", "danger")
                elif re_n2 < SS.v_news2:
                    AL("NEWS2 en baisse — Amélioration clinique", "success")

                if SS.t_reev:
                    mins = (datetime.now() - SS.t_reev).total_seconds() / 60
                    if 25 <= mins <= 35:
                        AL("⏱ Réévaluation douleur à 30 min POST-ANTALGIE — Obligatoire (Circulaire 2014)", "warning")
                    elif 55 <= mins <= 65:
                        AL("⏱ Réévaluation douleur à 60 min POST-ANTALGIE — Obligatoire", "warning")
                    delai_cible = {"M":5,"1":5,"2":15,"3A":30,"3B":60}.get(SS.niv, 60)
                    if mins > delai_cible:
                        AL(f"⏱ Délai cible Tri {SS.niv} dépassé ({delai_cible} min) — Relancer le médecin", "danger")

                if st.button("✅ Enregistrer la réévaluation", key=WK("save_reeval"), use_container_width=True):
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

            st.divider()
            CARD("Sécurité avant injection — Règle des 5B", "")
            st.caption("AR 78 sur l'exercice infirmier — AFMPS 2019")
            para_5b, _  = paracetamol(poids, age, atcd)
            nap_5b, _   = naproxene(poids, age, atcd)
            trad_5b, _  = tramadol(poids, age, atcd)
            dip_5b, _   = piritramide(poids, age, atcd)
            morph_5b, _ = morphine(poids, age, atcd)
            ves_5b, _   = vesiera(poids, age, atcd)
            gluc_5b, _  = glucose(poids, SS.gl, atcd) if SS.gl is not None else (None, None)
            _det_5b     = SS.det if isinstance(SS.det, dict) else {}
            dur_5b      = float(_det_5b.get("duree_min", 0) or 0)
            encours_5b  = bool(_det_5b.get("en_cours", False))
            eme_5b      = protocole_epilepsie_ped(poids, age, dur_5b, encours_5b, atcd)

            med_sel = st.selectbox("Médicament à injecter", [
                "Perfu — Paracétamol IV", "Naproxène PO", "Tradonal® — Tramadol",
                "Dipidolor® — Piritramide", "Morphine IV titrée", "Litican IM (40 mg)",
                "Adrénaline IM (0,5 mg)", "Ceftriaxone IV (2 g)", "Glucose 30 % IV",
                "Salbutamol nébulisation", "Furosémide IV", "Midazolam buccal",
                "Vesiera® — Kétamine perfusion", "Acide tranexamique IV (1 g)", "Autre",
            ], key="re_5b_med")

            doses_default = {
                "Perfu — Paracétamol IV":
                    (f"{(para_5b or {}).get('dose_display', '1 g')} IV en 15 min"),
                "Naproxène PO":
                    f"{(nap_5b or {}).get('dose_mg', 500):.0f} mg PO" if nap_5b else "500 mg PO",
                "Tradonal® — Tramadol":
                    f"{(trad_5b or {}).get('dose_mg', 50):.0f} mg PO" if trad_5b else "50 mg PO",
                "Dipidolor® — Piritramide":
                    (f"{(dip_5b or {}).get('dose_min',3):.1f}–"
                     f"{(dip_5b or {}).get('dose_max',6):.1f} mg IV lent") if dip_5b else "3–6 mg IV lent",
                "Morphine IV titrée":
                    (f"{(morph_5b or {}).get('dose_min',2):.1f}–"
                     f"{(morph_5b or {}).get('dose_max',7.5):.1f} mg IV titré") if morph_5b else "2–7,5 mg IV titré",
                "Litican IM (40 mg)":         "40 mg IM",
                "Adrénaline IM (0,5 mg)":     "0,5 mg IM cuisse antéro-latérale",
                "Ceftriaxone IV (2 g)":       "2 g IV en 3-5 min",
                "Glucose 30 % IV":
                    str((gluc_5b or {}).get("vol","Selon glycémie mesurée")) if gluc_5b else "Selon glycémie",
                "Salbutamol nébulisation":    "2,5–5 mg nébulisation",
                "Furosémide IV":              "40–80 mg IV lent",
                "Midazolam buccal":
                    str((eme_5b or {}).get("midazolam_buccal", {}).get("dose", "Selon poids")),
                "Vesiera® — Kétamine perfusion":
                    str((ves_5b or {}).get("dose","Selon protocole algologue")) if ves_5b else "Selon protocole",
                "Acide tranexamique IV (1 g)": "1 g IV en 10 min",
                "Autre": "À compléter",
            }
            dose_pre = st.text_input("Dose calculée",
                                      value=doses_default.get(med_sel,""), key="re_5b_dose")
            voie_pre = st.selectbox("Voie",
                ["IV","IM","SC","IN (intranasale)","Buccale","Nébulisation","PO"],
                key="re_5b_voie")
            CHECKLIST_5B(
                medicament=med_sel, dose=dose_pre, voie=voie_pre,
                poids=poids, uid=SS.uid_cur or SS.uid,
            )
            CARD_END()
            DISC()

        with ST[1]:
            reg = charger_registre()
            if reg:
                CARD("Statistiques session", "")
                s1, s2, s3 = st.columns(3)
                s1.metric("Patients", len(reg))
                s2.metric("Critiques (Tri M/1/2)",
                           sum(1 for r in reg if r.get("niv") in ("M","1","2")))
                s3.metric("NEWS2 moyen",
                           round(sum(r.get("n2",0) for r in reg) / len(reg), 1))
                CARD_END()

            CARD("Registre session (RGPD — anonyme)", "")
            if not reg:
                st.info("Aucun patient enregistré dans cette session")
            else:
                for r in reg[:20]:
                    c = st.columns([1, 3, 1, 1])
                    c[0].caption(r.get("heure","")[-5:])
                    c[1].write(r.get("motif",""))
                    c[2].write(f"**Tri {r.get('niv','')}**")
                    c[3].caption(r.get("uid",""))
            CARD_END()

            CARD("Export RGPD", "")
            if reg:
                out = io.StringIO()
                w   = csv_mod.writer(out)
                w.writerow(["uid","heure","motif","niv","n2","fc","pas",
                             "spo2","fr","temp","gcs","op"])
                for r in reg:
                    w.writerow([r.get(k,"") for k in
                                ["uid","heure","motif","niv","n2","fc","pas",
                                 "spo2","fr","temp","gcs","op"]])
                st.download_button(
                    "📥 Télécharger CSV", data=out.getvalue(),
                    file_name=f"akir_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv", use_container_width=True)

            if st.button("🔐 Vérifier intégrité audit", key=WK("audit_integrity"), use_container_width=True):
                audit = audit_verifier_integrite()
                AL(audit.get("message",""), "success" if audit.get("ok") else "danger")
            CARD_END()
            DISC()

        with ST[2]:
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

except Exception as e:
    st.error(f"🚨 Erreur critique dans l'application : {str(e)}")
    st.error("Veuillez contacter le développeur ou redémarrer l'application.")
    st.code(f"Traceback:\n{traceback.format_exc()}", language="text")
