from __future__ import annotations

from typing import Dict

import pandas as pd
import streamlit as st

from clinical.utils import norm


def EVA_WIDGET_COMPLET(key_prefix: str, age: float, non_communicant: bool = False) -> Dict[str, object]:
    st.markdown("### Evaluation de la douleur")
    if non_communicant:
        st.info("Patient potentiellement non communicant: corriger l'EVA par le contexte clinique et l'Algoplus.")

    eva = int(
        st.select_slider(
            "EVA",
            options=[str(i) for i in range(11)],
            value="0",
            key=f"{key_prefix}_eva",
        )
    )

    with st.expander("PQRST", expanded=False):
        p1, p2 = st.columns(2)
        p = p1.text_input("P - Facteurs declenchants / soulageants", key=f"{key_prefix}_p")
        q = p2.text_input("Q - Qualite", key=f"{key_prefix}_q", placeholder="brulure, colique, oppression")
        r = p1.text_input("R - Region / irradiation", key=f"{key_prefix}_r")
        s = p2.text_input("S - Severite complementaire", key=f"{key_prefix}_s", placeholder="continue, intermittente")
        t = st.text_input("T - Debut / evolution", key=f"{key_prefix}_t")

    return {
        "eva": eva,
        "pqrst": {"p": p, "q": q, "r": r, "s": s, "t": t},
    }


def SCHEMA_BRULURES(poids: float, age: float) -> Dict[str, object]:
    st.markdown("### Brulures")
    c1, c2 = st.columns(2)
    surface_pct = c1.slider("Surface brulee estimee (%)", 0, 100, 0, key="br_surface")
    profondeur = c2.selectbox("Profondeur dominante", ["1er degre", "2e degre", "3e degre"], key="br_prof")
    baux = int(age) + surface_pct
    st.caption(f"Indice de Baux estime: {baux}")
    return {"surface_pct": surface_pct, "baux": baux, "profondeur": profondeur}


def QUESTIONS_AVANCEES(
    motif: str,
    details: Dict[str, object],
    age: float,
    atcd: list,
    poids: float,
    gl_global,
) -> Dict[str, object]:
    details = dict(details or {})
    m = norm(motif)
    st.markdown("### Questions discriminantes")

    if "douleur thoracique" in m or "sca" in m:
        c1, c2 = st.columns(2)
        details["douleur_type"] = c1.selectbox(
            "Type de douleur thoracique",
            ["Atypique", "Coronaire probable", "Typique"],
            key="qa_dt",
        )
        details["ecg_anormal"] = c2.checkbox("ECG anormal", key="qa_ecg")
        details["troponine_pos"] = c1.checkbox("Troponine positive", key="qa_trop")
        details["frcv"] = c2.number_input("Nombre de FRCV", 0, 6, 0, key="qa_frcv")

    if "douleur abdominale" in m:
        c1, c2 = st.columns(2)
        details["defense"] = c1.checkbox("Defense abdominale", key="qa_def")
        details["grossesse"] = c2.checkbox("Grossesse suspectee / connue", key="qa_gross")
        details["douleur_severe"] = c1.checkbox("Douleur severe ou mal toleree", key="qa_abd_sev")
        details["vomissements"] = c2.checkbox("Vomissements associes", key="qa_abd_vom")

    if "colique" in m or "lombaire" in m:
        c1, c2 = st.columns(2)
        details["fievre"] = c1.checkbox("Fievre associee", key="qa_col_f")
        details["douleur_lombaire"] = c2.checkbox("Douleur lombaire franche", key="qa_col_l")
        details["hematurie"] = c1.checkbox("Hematurie", key="qa_col_h")
        details["vomissements"] = c2.checkbox("Vomissements", key="qa_col_v")

    if "dyspnee" in m:
        c1, c2 = st.columns(2)
        details["tirage"] = c1.checkbox("Tirage / effort respiratoire", key="qa_dy_t")
        details["cyanose"] = c2.checkbox("Cyanose", key="qa_dy_c")
        details["parole_ok"] = c1.checkbox("Parle en phrases completes", value=True, key="qa_dy_p")

    if "convulsions" in m or "crise epileptique" in m or "eme" in m:
        c1, c2, c3 = st.columns(3)
        details["duree_min"] = c1.number_input(
            "Duree de crise (min)",
            0.0,
            120.0,
            float(details.get("duree_min", 0.0) or 0.0),
            0.5,
            key="qa_em_duree",
        )
        details["en_cours"] = c2.checkbox(
            "Crise en cours",
            value=bool(details.get("en_cours", False)),
            key="qa_em_encours",
        )
        details["recuperee"] = c3.checkbox(
            "Crise recuperee",
            value=bool(details.get("recuperee", False)),
            key="qa_em_recup",
        )
        c4, c5, c6 = st.columns(3)
        details["premiere_crise"] = c4.checkbox("Premiere crise", key="qa_em_first")
        details["focale"] = c5.checkbox("Composante focale", key="qa_em_foc")
        details["febrile"] = c6.checkbox("Contexte febrile", key="qa_em_febr")
        c7, c8 = st.columns(2)
        details["signes_meninges"] = c7.checkbox("Signes meninges", key="qa_em_men")
        details["eme_etabli"] = c8.checkbox(
            "EME etabli",
            value=bool((details.get("duree_min", 0) or 0) >= 30),
            key="qa_em_etab",
        )
        if gl_global is None:
            gl_local = st.number_input("Glycemie capillaire (mg/dl)", 0, 1500, 0, 5, key="qa_em_gl")
            if gl_local > 0:
                details["glycemie_mgdl"] = float(gl_local)

    if "fievre" in m and "crise epileptique" not in m:
        c1, c2 = st.columns(2)
        details["signes_meninges"] = c1.checkbox("Signes meninges", key="qa_f_men")
        details["purpura"] = c2.checkbox("Purpura / petechies non effacables", key="qa_f_purp")

    return details


def PRESCRIPTIONS_ANTICIPEES(
    motif: str,
    niv: str,
    poids: float,
    age: float,
    atcd: list,
    eva: int,
    spo2: float,
    pas: float,
):
    suggestions = []
    m = norm(motif)
    if eva >= 4:
        suggestions.append("Antalgie IAO selon protocole EVA")
    if "convulsions" in m or "crise epileptique" in m or "eme" in m:
        suggestions.append("Preparer midazolam et monitorage")
    if "fievre" in m and pas < 90:
        suggestions.append("Antibiotherapie / bundle sepsis a discuter en urgence")
    if "dyspnee" in m and spo2 < 92:
        suggestions.append("Oxygene, scope et appel medical rapide")

    if suggestions:
        with st.expander("Prescriptions anticipees IAO", expanded=False):
            for item in suggestions:
                st.checkbox(item, value=False, key=f"pa_{norm(item)}")
    return {"niveau": niv, "items": suggestions} if suggestions else None


def COURBE_VITAUX(reevs) -> None:
    if not reevs:
        return
    st.markdown("### Evolution temporelle")
    df = pd.DataFrame(reevs)
    if "h" in df.columns:
        df = df.set_index("h")
    numeric_cols = [c for c in ["n2", "fc", "pas", "spo2", "fr", "temp"] if c in df.columns]
    if numeric_cols:
        st.line_chart(df[numeric_cols])
    st.dataframe(df.reset_index(), use_container_width=True)


def CHECKLIST_5B(medicament: str, dose: str, voie: str, poids: float, uid: str) -> None:
    st.caption(f"Patient/session: {uid} - Poids de reference: {poids} kg")
    checks = [
        st.checkbox("Bon patient", key="5b_patient"),
        st.checkbox("Bon medicament", key="5b_med"),
        st.checkbox("Bonne dose", key="5b_dose"),
        st.checkbox("Bonne voie", key="5b_voie"),
        st.checkbox("Bon moment / bonne indication", key="5b_moment"),
    ]
    st.text_input("Trace resumee", value=f"{medicament} | {dose} | {voie}", key="5b_trace")
    if all(checks):
        st.success("Checklist 5B completee")

