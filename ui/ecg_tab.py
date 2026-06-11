# ui/ecg_tab.py — Onglet ECG (aide à la priorisation IAO) — AKIR-IAO v21
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
#
# Étape 3 de la finalisation ECG : la vue. Elle relie predictor + garde-fous +
# taxonomie honnête, et impose deux sécurités UX :
#   - signalement de la FIABILITÉ par classe (data_support) ;
#   - CONFIRMATION explicite avant d'injecter la priorité dans le triage.
#
# Contrat : streamlit_app.py (onglet 7) fait `from ui.ecg_tab import render`.
# RGPD : aucune image ni donnée nominative persistée — traitement en mémoire.
# Outil expérimental d'aide à la décision — confirmation cardiologue obligatoire.

from __future__ import annotations

import streamlit as st

from clinical.ecg_labels import display_name, data_support, FULL, PARTIAL

_PRIO_LIBELLE = {
    1: ("P1", "Détresse vitale — prise en charge immédiate", "#DC2626"),
    2: ("P2", "Très urgent", "#EA580C"),
    3: ("P3", "Urgent", "#CA8A04"),
    4: ("P4", "Peu urgent", "#16A34A"),
    5: ("P5", "Non urgent", "#2563EB"),
}


def _badge_priorite(prio: int) -> None:
    code, libelle, couleur = _PRIO_LIBELLE.get(prio, ("?", "Indéterminé", "#64748B"))
    st.markdown(
        f"<div style='background:{couleur};color:#fff;border-radius:10px;"
        f"padding:14px 18px;font-weight:700;font-size:1.05rem;text-align:center'>"
        f"{code} — {libelle}</div>",
        unsafe_allow_html=True,
    )


def _avert_fiabilite(support: str) -> None:
    if support == FULL:
        return
    msg = {
        PARTIAL: "Fiabilité limitée — cette classe est partiellement couverte par "
                 "les données d'entraînement. À confirmer cliniquement.",
    }.get(
        support,
        "Fiabilité NON garantie — cette classe est quasi absente des données "
        "d'entraînement. Ne pas s'y fier ; interprétation médicale requise.",
    )
    st.warning(msg)


def render() -> None:
    st.subheader("📷 ECG — aide à la priorisation")
    st.caption(
        "Outil **expérimental** d'aide à la décision. Confirmation cardiologue "
        "**obligatoire**. Aucune image ni donnée nominative n'est enregistrée."
    )

    age = st.number_input("Âge du patient (ans)", min_value=0, max_value=120, value=50)

    source = st.camera_input("Photographier l'ECG 12 dérivations")
    if source is None:
        source = st.file_uploader(
            "…ou importer une image d'ECG", type=["jpg", "jpeg", "png"]
        )
    if source is None:
        st.info("Capturez ou importez un ECG pour lancer l'analyse.")
        return

    # ── Inférence (le predictor dégrade proprement si torch/poids absents) ──
    try:
        from ml.ecg_predictor import predict_ecg
    except Exception:
        st.error("Module ECG indisponible (dépendances non installées).")
        return

    with st.spinner("Analyse de l'ECG…"):
        res = predict_ecg(source.getvalue(), age_years=age)

    if res.get("erreur"):
        st.warning(res["erreur"])
        return

    verdict = res["verdict"]
    probs = res["probabilities"]

    # ── Abstention pédiatrique (R0) ──────────────────────────────────────
    if verdict.get("abstain"):
        st.info(verdict.get("override", "Abstention — interprétation médicale requise."))
        return

    # ── Priorité + garde-fou déclenché ───────────────────────────────────
    _badge_priorite(verdict["priorite"])
    if verdict.get("override"):
        st.markdown(f"🛡️ **Garde-fou appliqué** — {verdict['override']}")
    if verdict.get("critical_flags"):
        st.error("Signe(s) critique(s) : " + ", ".join(verdict["critical_flags"]))

    # ── Fiabilité de la classe dominante ─────────────────────────────────
    _avert_fiabilite(verdict.get("data_support", FULL))

    # ── Probabilités (libellés honnêtes, triées) ─────────────────────────
    st.markdown("**Lecture du modèle** (probabilités) :")
    top = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)[:5]
    for label, p in top:
        marqueur = "" if data_support(label) == FULL else " ⚠️"
        st.write(f"- {display_name(label)} — {p:.0%}{marqueur}")

    st.divider()

    # ── Confirmation explicite avant injection dans le triage ────────────
    st.caption(
        "L'injection remplace la priorité de triage courante. Action à valider "
        "par l'IAO après lecture du tracé."
    )
    if st.button("✅ Injecter la priorité dans le triage", use_container_width=True):
        st.session_state["ecg_priorite"] = verdict["priorite"]
        st.session_state["ecg_override"] = verdict.get("override")
        st.success(
            f"Priorité P{verdict['priorite']} transmise au triage "
            "(modifiable manuellement)."
        )
