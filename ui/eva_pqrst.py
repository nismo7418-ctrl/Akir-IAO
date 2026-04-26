# ui/eva_pqrst.py — Évaluation douleur et questions discriminantes — AKIR-IAO v19.0
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Source : Circulaire belge réévaluation douleur 2014, protocoles SFMU

from __future__ import annotations
from typing import Dict, Optional
import pandas as pd
import streamlit as st
from clinical.utils import norm


# ═══════════════════════════════════════════════════════════════════════════════
# EVA — Évaluation de la douleur
# ═══════════════════════════════════════════════════════════════════════════════

def EVA_WIDGET_COMPLET(key_prefix: str, age: float, non_communicant: bool = False) -> Dict:
    """
    Widget complet d'évaluation de la douleur — EVA + PQRST.
    Retourne {eva, pqrst}.
    Source : Circulaire belge réévaluation douleur 2014.
    """
    st.markdown("### Évaluation de la douleur")

    if non_communicant:
        st.info("Patient potentiellement non communicant — Corriger l'EVA par le contexte clinique et l'Algoplus (Rat P, 2011).")

    eva = int(st.select_slider(
        "EVA / NRS",
        options=[str(i) for i in range(11)],
        value="0",
        key=f"{key_prefix}_eva",
        help="0 = pas de douleur | 10 = douleur insupportable",
    ))

    # Feedback couleur selon EVA
    if eva >= 7:
        st.error(f"🔴 Douleur sévère EVA {eva}/10 — Antalgie forte requise")
    elif eva >= 4:
        st.warning(f"🟠 Douleur modérée EVA {eva}/10 — Antalgie à initier")
    elif eva >= 1:
        st.info(f"🔵 Douleur légère EVA {eva}/10 — Surveillance et antalgique palier 1")
    else:
        st.success("🟢 EVA 0/10 — Pas de douleur déclarée")

    with st.expander("📋 Questionnaire PQRST", expanded=False):
        p1, p2 = st.columns(2)
        p = p1.text_input("P — Facteurs déclenchants / soulageants",
                          key=f"{key_prefix}_p",
                          placeholder="effort, repos, position...")
        q = p2.text_input("Q — Qualité / type",
                          key=f"{key_prefix}_q",
                          placeholder="brûlure, colique, oppression...")
        r = p1.text_input("R — Région / irradiation",
                          key=f"{key_prefix}_r",
                          placeholder="thorax, bras gauche, jambe...")
        s = p2.text_input("S — Sévérité complémentaire",
                          key=f"{key_prefix}_s",
                          placeholder="continue, intermittente, pulsatile...")
        t = st.text_input("T — Début / évolution temporelle",
                          key=f"{key_prefix}_t",
                          placeholder="brutal, progressif, depuis 2h...")

    return {
        "eva": eva,
        "pqrst": {"p": p if "p" in dir() else "", "q": q if "q" in dir() else "",
                  "r": r if "r" in dir() else "", "s": s if "s" in dir() else "",
                  "t": t if "t" in dir() else ""},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMA DES BRÛLURES
# ═══════════════════════════════════════════════════════════════════════════════

def SCHEMA_BRULURES(poids: float, age: float) -> Dict:
    """
    Évaluation des brûlures — Règle des 9 de Wallace + Indice de Baux.
    Source : Wallace AB, Lancet 1951.
    """
    st.markdown("### 🔥 Évaluation des brûlures")

    c1, c2 = st.columns(2)
    surface_pct = c1.slider("Surface brûlée estimée (%)", 0, 100, 0, key="br_surface",
                             help="Règle des 9 de Wallace : Tête=9%, chaque membre sup=9%, torse ant/post=18%, chaque MI=18%, périnée=1%")
    profondeur  = c2.selectbox("Profondeur dominante",
                               ["1er degré (érythème)", "2e degré superficiel", "2e degré profond", "3e degré"],
                               key="br_prof")

    baux = int(age) + surface_pct
    c1.caption(f"Indice de Baux : {baux} (âge + surface) — Mortalité estimée ≈ {baux}%")

    if surface_pct > 25:
        st.error(f"🔴 Brûlure étendue {surface_pct}% — Transfert centre grand brûlé à discuter")
    elif surface_pct > 15:
        st.warning(f"🟠 Brûlure {surface_pct}% — Hospitalisation et bilan hydroélectrolytique")
    elif surface_pct > 5:
        st.info(f"🔵 Brûlure localisée {surface_pct}%")

    return {"surface_pct": surface_pct, "baux": baux, "profondeur": profondeur}


# ═══════════════════════════════════════════════════════════════════════════════
# QUESTIONS DISCRIMINANTES AVANCÉES
# ═══════════════════════════════════════════════════════════════════════════════

def QUESTIONS_AVANCEES(
    motif: str,
    details: Dict,
    age: float,
    atcd: list,
    poids: float,
    gl_global=None,
) -> Dict:
    """
    Questions discriminantes adaptées au motif de recours.
    Retourne le dict details enrichi.
    Source : SFMU FRENCH V1.1 — Arbres de décision clinique.
    """
    details = dict(details or {})
    m = norm(motif)
    st.markdown("### Questions discriminantes")

    # ── Douleur thoracique / SCA ──────────────────────────────────────────
    if "douleur thoracique" in m or "sca" in m:
        c1, c2 = st.columns(2)
        details["douleur_type"] = c1.selectbox(
            "Type de douleur", ["Atypique", "Coronaire probable", "Typique"], key="qa_dt")
        details["ecg_anormal"]  = c2.checkbox("ECG anormal", key="qa_ecg")
        details["troponine_pos"] = c1.checkbox("Troponine positive", key="qa_trop")
        details["frcv"]         = c2.number_input("Nombre de FRCV", 0, 6, 0, key="qa_frcv")
        details["typique"]      = details["douleur_type"] == "Typique"

    # ── Douleur abdominale ────────────────────────────────────────────────
    if "douleur abdominale" in m:
        c1, c2 = st.columns(2)
        details["defense"]        = c1.checkbox("Défense abdominale", key="qa_def")
        details["grossesse"]      = c2.checkbox("Grossesse suspectée / connue", key="qa_gross")
        details["douleur_severe"] = c1.checkbox("Douleur sévère ou mal tolérée", key="qa_abd_sev")
        details["vomissements"]   = c2.checkbox("Vomissements associés", key="qa_abd_vom")
        if details.get("grossesse"):
            st.error("🔴 Grossesse + douleur abdominale — GEU à exclure — Beta-hCG URGENT")

    # ── Colique néphrétique ───────────────────────────────────────────────
    if "colique" in m or "lombaire" in m:
        c1, c2 = st.columns(2)
        details["fievre"]          = c1.checkbox("Fièvre associée", key="qa_col_f")
        details["douleur_lombaire"] = c2.checkbox("Douleur lombaire franche", key="qa_col_l")
        details["hematurie"]        = c1.checkbox("Hématurie", key="qa_col_h")
        details["vomissements"]     = c2.checkbox("Vomissements", key="qa_col_v")
        if details.get("fievre"):
            st.error("🔴 Colique fébrile — Pyélonéphrite obstructive à exclure — Tri 2")

    # ── Dyspnée ───────────────────────────────────────────────────────────
    if "dyspnee" in m or "insuffisance respiratoire" in m:
        c1, c2 = st.columns(2)
        details["tirage"]    = c1.checkbox("Tirage / effort respiratoire", key="qa_dy_t")
        details["cyanose"]   = c2.checkbox("Cyanose", key="qa_dy_c")
        details["parole_ok"] = c1.checkbox("Parle en phrases complètes", value=True, key="qa_dy_p")
        details["orthopnee"] = c2.checkbox("Orthopnée (dort assis)", key="qa_dy_o")
        if details.get("cyanose"):
            st.error("🔴 Cyanose — SpO2 critique — O2 haut débit IMMÉDIAT")

    # ── AVC ───────────────────────────────────────────────────────────────
    if "avc" in m or "deficit neurologique" in m or "deficit moteur" in m:
        c1, c2 = st.columns(2)
        details["fast_positif"]     = c1.checkbox("BE-FAST positif (face/bras/parole)", key="qa_avc_fast")
        details["heure_debut"]      = c2.text_input("Heure dernière fois vu bien", key="qa_avc_h", placeholder="ex: 14:30")
        details["hemiplegique"]     = c1.checkbox("Hémiplégie franche", key="qa_avc_hemi")
        details["aphasie"]          = c2.checkbox("Aphasie / trouble du langage", key="qa_avc_aph")
        if details.get("fast_positif"):
            st.error("🔴 BE-FAST positif — CODE STROKE IMMÉDIAT — Filière thrombolyse")

    # ── Traumatisme crânien ───────────────────────────────────────────────
    if "traumatisme cranien" in m or "tc" in m:
        c1, c2 = st.columns(2)
        details["perte_connaissance"]          = c1.checkbox("Perte de connaissance", key="qa_tc_pdc")
        details["vomissements"]                = c2.checkbox("Vomissements", key="qa_tc_vom")
        details["perte_connaissance_prolongee"] = c1.checkbox("PDC prolongée (> 5 min)", key="qa_tc_pdcp")
        details["anticoagulants"]              = c2.checkbox("Sous anticoagulants / AOD", key="qa_tc_aod")
        details["cephalee_post_tc"]            = c1.checkbox("Céphalée post-TC", key="qa_tc_cep")

    # ── Fièvre ────────────────────────────────────────────────────────────
    if "fievre" in m and "crise epileptique" not in m:
        c1, c2 = st.columns(2)
        details["signes_meninges"] = c1.checkbox("Signes méningés / raideur nuque", key="qa_f_men")
        details["purpura"]         = c2.checkbox("Purpura / pétéchies non effaçables", key="qa_f_purp")
        details["confusion"]       = c1.checkbox("Confusion / désorientation", key="qa_f_conf")
        if details.get("purpura"):
            st.error("🔴 PURPURA FULMINANS SUSPECTÉ — Ceftriaxone IMMÉDIAT")
        if details.get("signes_meninges"):
            st.error("🔴 Méningite suspecte — Bilan urgent + antibiothérapie précoce")

    # ── Convulsions / EME ─────────────────────────────────────────────────
    if "convulsions" in m or "crise epileptique" in m or "eme" in m:
        c1, c2, c3 = st.columns(3)
        details["duree_min"] = c1.number_input(
            "Durée de crise (min)", 0.0, 120.0,
            float(details.get("duree_min", 0.0) or 0.0), 0.5, key="qa_em_duree")
        details["en_cours"]   = c2.checkbox("Crise en cours", value=bool(details.get("en_cours", False)), key="qa_em_encours")
        details["recuperee"]  = c3.checkbox("Crise récupérée", value=bool(details.get("recuperee", False)), key="qa_em_recup")
        c4, c5, c6 = st.columns(3)
        details["premiere_crise"] = c4.checkbox("Première crise", key="qa_em_first")
        details["focale"]         = c5.checkbox("Composante focale", key="qa_em_foc")
        details["febrile"]        = c6.checkbox("Contexte fébrile", key="qa_em_febr")
        c7, c8 = st.columns(2)
        details["signes_meninges"] = c7.checkbox("Signes méningés", key="qa_em_men")
        details["eme_etabli"]      = c8.checkbox("EME établi",
            value=bool((details.get("duree_min", 0) or 0) >= 30), key="qa_em_etab")
        if details.get("en_cours"):
            st.error("🔴 CRISE EN COURS — Anticonvulsivant IMMÉDIAT — Voir onglet Pharmacie")
        if gl_global is None:
            gl_local = st.number_input("Glycémie capillaire (mg/dl)", 0, 1500, 0, 5, key="qa_em_gl")
            if gl_local > 0:
                details["glycemie_mgdl"] = float(gl_local)

    # ── Allergie / Anaphylaxie ────────────────────────────────────────────
    if "allergie" in m or "anaphylaxie" in m:
        c1, c2 = st.columns(2)
        details["dyspnee"]            = c1.checkbox("Dyspnée / stridor", key="qa_ana_dy")
        details["mauvaise_tolerance"] = c2.checkbox("Hypotension / malaise", key="qa_ana_ht")
        details["urticaire_generalisee"] = c1.checkbox("Urticaire généralisée", key="qa_ana_urt")
        if details.get("dyspnee") or details.get("mauvaise_tolerance"):
            st.error("🔴 Anaphylaxie sévère — Adrénaline IM IMMÉDIAT 0.5 mg cuisse")

    # ── Hémorragie / Purpura ──────────────────────────────────────────────
    if "hemorragie" in m or "rectorragie" in m or "hematemese" in m:
        c1, c2 = st.columns(2)
        details["abondante"] = c1.checkbox("Saignement abondant actif", key="qa_hem_ab")
        details["active"]    = c2.checkbox("Saignement en cours", key="qa_hem_act")

    if "purpura" in m or "petechie" in m:
        details["non_effacable"] = st.checkbox("Purpura / pétéchies NON effaçables (test du verre)", key="qa_pur_ne")
        details["neff"]          = details.get("non_effacable", False)

    # ── Brûlure ───────────────────────────────────────────────────────────
    if "brulure" in m:
        c1, c2 = st.columns(2)
        details["voies_aeriennes"] = c1.checkbox("Brûlure voies aériennes suspecte", key="qa_br_va")
        details["troisieme_degre"] = c2.checkbox("3e degré", key="qa_br_3d")
        details["visage"]          = c1.checkbox("Visage / mains", key="qa_br_vis")

    # ── Épistaxis ────────────────────────────────────────────────────────
    if "epistaxis" in m:
        c1, c2 = st.columns(2)
        details["abondant_actif"]     = c1.checkbox("Abondant actif", key="qa_ep_act")
        details["abondant_resolutif"] = c2.checkbox("Abondant résolutif", key="qa_ep_res")

    # ── Hypoglycémie ──────────────────────────────────────────────────────
    if "hypoglycemie" in m:
        if gl_global is None:
            gl_l = st.number_input("Glycémie capillaire (mg/dl)", 0, 500, 0, 5, key="qa_hg_gl")
            if gl_l > 0:
                details["glycemie_mgdl"] = float(gl_l)

    return details


# ═══════════════════════════════════════════════════════════════════════════════
# PRESCRIPTIONS ANTICIPÉES
# ═══════════════════════════════════════════════════════════════════════════════

def PRESCRIPTIONS_ANTICIPEES(
    motif: str,
    niv: str,
    poids: float,
    age: float,
    atcd: list,
    eva: int,
    spo2: float,
    pas: float,
) -> Optional[dict]:
    """
    Prescriptions anticipées IAO selon motif et niveau de triage.
    Source : Protocoles locaux Hainaut / SFMU / BCFI.
    """
    suggestions = []
    m = norm(motif)

    if eva >= 4:
        suggestions.append("Antalgie IAO selon protocole EVA")
    if "avc" in m or "deficit neurologique" in m or "deficit moteur" in m:
        suggestions.append("Alerte filière Stroke — Glycémie capillaire urgente")
    if "convulsions" in m or "crise epileptique" in m or "eme" in m:
        suggestions.append("Préparer midazolam buccal + monitorage")
    if "fievre" in m and pas < 90:
        suggestions.append("Antibiothérapie / bundle sepsis à discuter en urgence")
    if "dyspnee" in m and spo2 < 92:
        suggestions.append("O2 haut débit — Scope — Appel médical rapide")
    if "douleur thoracique" in m or "sca" in m:
        suggestions.append("ECG 12 dérivations — Aspirine 250 mg si non contre-indiqué")
    if "hypoglycemie" in m:
        suggestions.append("Glycémie capillaire — Resucrage IV / PO selon état de conscience")
    if "allergie" in m or "anaphylaxie" in m:
        suggestions.append("Adrénaline IM 0.5 mg prête — Vérifier tolérance hémodynamique")

    if suggestions:
        with st.expander("💊 Prescriptions anticipées IAO", expanded=False):
            st.caption("Cocher les prescriptions anticipées initiées")
            for item in suggestions:
                st.checkbox(item, value=False, key=f"pa_{norm(item)[:30]}")

    return {"niveau": niv, "items": suggestions} if suggestions else None


# ═══════════════════════════════════════════════════════════════════════════════
# COURBE TEMPORELLE DES VITAUX (Réévaluation)
# ═══════════════════════════════════════════════════════════════════════════════

def COURBE_VITAUX(reevs: list) -> None:
    """
    Courbe temporelle des vitaux lors des réévaluations.
    Source : Obligation de traçabilité — Circulaire belge 2014.
    """
    if not reevs:
        return
    st.markdown("### 📈 Évolution temporelle des vitaux")
    try:
        df = pd.DataFrame(reevs)
        if "h" in df.columns:
            df = df.set_index("h")
        numeric_cols = [c for c in ["n2", "fc", "pas", "spo2", "fr", "temp"] if c in df.columns]
        col_labels = {"n2": "NEWS2", "fc": "FC (bpm)", "pas": "PAS (mmHg)", "spo2": "SpO2 (%)", "fr": "FR/min", "temp": "T°C"}
        df_renamed = df[numeric_cols].rename(columns=col_labels)
        if len(df_renamed) > 1:
            st.line_chart(df_renamed)
        st.dataframe(df.reset_index(), use_container_width=True)
    except Exception as e:
        st.warning(f"Courbe non disponible : {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKLIST 5B — Sécurité avant injection
# ═══════════════════════════════════════════════════════════════════════════════

def CHECKLIST_5B(medicament: str, dose: str, voie: str, poids: float, uid: str) -> None:
    """
    Checklist 5B — Obligatoire avant toute injection médicamenteuse.
    Source : AR 78 sur l'exercice infirmier — AFMPS 2019.
    """
    st.caption(f"Session : {uid} — Poids de référence : {poids} kg")
    checks = [
        st.checkbox("✅ Bon patient (identité confirmée)", key="5b_patient"),
        st.checkbox("✅ Bon médicament", key="5b_med"),
        st.checkbox("✅ Bonne dose", key="5b_dose"),
        st.checkbox("✅ Bonne voie", key="5b_voie"),
        st.checkbox("✅ Bon moment / bonne indication", key="5b_moment"),
    ]
    st.text_input(
        "Traçabilité résumée (à valider)",
        value=f"{medicament} | {dose} | {voie}",
        key="5b_trace",
    )
    if all(checks):
        st.success("✅ Checklist 5B complétée — Injection autorisée — Heure : " +
                   __import__("datetime").datetime.now().strftime("%H:%M"))
    else:
        remaining = 5 - sum(checks)
        st.warning(f"⚠️ {remaining} critère(s) non validé(s) — Vérifier avant injection")
