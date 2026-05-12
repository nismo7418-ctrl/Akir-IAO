# clinical/triage_handlers/pediatrie.py — Module triage pédiatrique — AKIR-IAO v20
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Sources : SFP/SFMU 2017 · HAS 2019 Bronchiolite · SFNP 2023 · GINA 2023
#           ESPGHAN 2014 · ATLS 11th · PHTLS 10th · PEWS Monaghan 2005

from __future__ import annotations

import streamlit as st

from clinical.triage import (
    _h_ped_fievre_nourr,
    _h_ped_fievre,
    _h_ped_gastro,
    _h_ped_epilepsie,
    _h_ped_asthme,
    _h_ped_bronchiolite,
    _h_ped_deshydratation,
    _h_ped_douleur_abdominale,
    _h_ped_trauma,
    _fc_tachy_ped,
)
from clinical.news2 import calculer_pews as _pews_vitaux, seuils_normaux_ped
from clinical.tools import broselow

SS = st.session_state

# ── Catalogue des motifs pédiatriques avec handler associé ───────────────────
MOTIFS_PED = {
    "Fièvre ≤ 3 mois":              _h_ped_fievre_nourr,
    "Fièvre enfant (3 mois – 15 ans)": _h_ped_fievre,
    "Vomissements / Gastro-entérite": _h_ped_gastro,
    "Crise épileptique":             _h_ped_epilepsie,
    "Asthme / Bronchospasme":        _h_ped_asthme,
    "Bronchiolite":                  _h_ped_bronchiolite,
    "Déshydratation":                _h_ped_deshydratation,
    "Douleur abdominale":            _h_ped_douleur_abdominale,
    "Traumatisme pédiatrique":       _h_ped_trauma,
}


def _badge(val, lo: float, hi: float, unit: str) -> str:
    """Badge coloré valeur normale/anormale."""
    ok = (lo <= val <= hi) if val is not None else True
    c = "#22C55E" if ok else "#EF4444"
    return (
        f"<div style='font-size:.72rem;color:{c};font-weight:700;'>"
        f"{val or '?'} {unit}"
        f"<br><span style='color:#64748B;font-weight:400;'>({lo:.0f}-{hi:.0f})</span></div>"
    )


def _pews_badge(score: int) -> str:
    if score >= 7:
        col, lbl = "#7C3AED", f"PEWS {score} — CRITIQUE"
    elif score >= 5:
        col, lbl = "#EF4444", f"PEWS {score} — ÉLEVÉ"
    elif score >= 3:
        col, lbl = "#F59E0B", f"PEWS {score} — MODÉRÉ"
    else:
        col, lbl = "#22C55E", f"PEWS {score} — STABLE"
    return (
        f"<div style='background:{col}20;border:2px solid {col};"
        f"border-radius:10px;padding:10px 16px;text-align:center;margin:8px 0;'>"
        f"<div style='font-size:2rem;font-weight:900;color:{col};"
        f"font-family:monospace;'>{score}/9</div>"
        f"<div style='font-size:.72rem;font-weight:700;color:{col};'>{lbl}</div>"
        f"</div>"
    )


# ─────────────────────────────────────────────────────────────────────────────
# COMPOSANT PRINCIPAL — appelable depuis n'importe quel onglet Streamlit
# ─────────────────────────────────────────────────────────────────────────────

def triage_pediatrie(age: float | None = None, poids: float | None = None) -> None:
    """
    Widget de triage pédiatrique complet.

    Affiche :
    - Valeurs normales par âge + badges d'alerte
    - PEWS (Paediatric Early Warning Score)
    - Broselow si taille saisie
    - Triage par motif avec résultat FRENCH
    - Actions immédiates contextuelles
    """
    _age   = float(age   or SS.get("age",   1.0))
    _poids = float(poids or SS.get("poids", 10.0))

    st.markdown("### 👶 Module Triage Pédiatrique")
    st.caption(f"Patient : {_age:.1f} ans · {_poids:.1f} kg")

    if _age >= 16:
        st.info("Ce module est réservé aux patients de moins de 16 ans.")
        return

    # ── A) Valeurs normales pour l'âge ───────────────────────────────────────
    sv = seuils_normaux_ped(_age)
    st.markdown(
        f"<div style='font-size:.72rem;font-weight:700;color:#64748B;"
        f"text-transform:uppercase;margin-bottom:4px;'>"
        f"Valeurs normales — {sv['label']}</div>",
        unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(_badge(SS.get("v_fc"),  *sv["fc"],  "bpm"),  unsafe_allow_html=True)
    c2.markdown(_badge(SS.get("v_pas"), *sv["pas"], "mmHg"), unsafe_allow_html=True)
    c3.markdown(_badge(SS.get("v_fr"),  *sv["fr"],  "/min"), unsafe_allow_html=True)
    spo2_ok = (SS.get("v_spo2") or 98) >= sv["spo2_min"]
    spo2_c  = "#22C55E" if spo2_ok else "#EF4444"
    c4.markdown(
        f"<div style='font-size:.72rem;color:{spo2_c};font-weight:700;'>"
        f"{SS.get('v_spo2','?')} %"
        f"<br><span style='color:#64748B;font-weight:400;'>(≥{sv['spo2_min']})</span></div>",
        unsafe_allow_html=True)

    # Tachycardie pédiatrique
    fc_val = SS.get("v_fc") or 0
    if fc_val and _fc_tachy_ped(fc_val, _age):
        st.warning(f"⚠️ Tachycardie pédiatrique — FC {fc_val} bpm pour {_age:.1f} ans")

    st.divider()

    # ── B) PEWS ──────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:.75rem;font-weight:700;color:#64748B;"
        "text-transform:uppercase;'>PEWS — Paediatric Early Warning Score</div>",
        unsafe_allow_html=True)
    st.caption("Monaghan A, Paediatric Nursing 2005")

    p1, p2, p3 = st.columns(3)
    _pw_co = p1.select_slider(
        "Comportement", [0,1,2,3,4],
        format_func=lambda x: {0:"Normal",1:"Dormant",2:"Irritable",
                                3:"Conscience réduite",4:"Inconscient"}[x],
        key="ped_pews_co")
    _pw_ca = p2.select_slider(
        "Cardiovasculaire", [0,1,2,3],
        format_func=lambda x: {0:"Rosé TRC≤2s",1:"Pâle TRC>2s",
                                2:"Gris TRC≥3s",3:"Gris+tachycardie"}[x],
        key="ped_pews_ca")
    _pw_re = p3.select_slider(
        "Respiratoire", [0,1,2,3],
        format_func=lambda x: {0:"Normal",1:"Tachypnée",
                                2:"Tirage modéré",3:"Tirage sévère"}[x],
        key="ped_pews_re")

    pews_score = int(_pw_co) + int(_pw_ca) + int(_pw_re)
    st.markdown(_pews_badge(pews_score), unsafe_allow_html=True)

    if pews_score >= 7:
        st.error("🔴 PEWS ≥ 7 — APPEL ÉQUIPE RÉANIMATION PÉDIATRIQUE IMMÉDIAT")
    elif pews_score >= 5:
        st.error("🟠 PEWS ≥ 5 — APPEL MÉDECIN IMMÉDIAT (< 5 min)")
    elif pews_score >= 3:
        st.warning("🟡 PEWS ≥ 3 — Surveillance rapprochée, réévaluation < 30 min")

    st.divider()

    # ── C) Broselow (si taille disponible) ───────────────────────────────────
    _taille = float(SS.get("taille") or 0)
    if 40 <= _taille <= 160:
        br = broselow(_taille)
        br_col = br.get("hex_couleur", "#64748B")
        st.markdown(
            f"<div style='background:{br_col};border-radius:10px;"
            f"padding:10px 16px;margin:6px 0;display:flex;"
            f"justify-content:space-between;align-items:center;'>"
            f"<div style='font-size:1rem;font-weight:900;color:#0F172A;'>"
            f"Broselow — {br['couleur'].upper()}</div>"
            f"<div style='font-size:.78rem;color:#1E293B;'>"
            f"Poids estimé : {br['poids_estimé']} kg</div>"
            f"</div>",
            unsafe_allow_html=True)
        if br.get("doses"):
            with st.expander("📋 Doses Broselow", expanded=False):
                for nom_d, val_d in br["doses"].items():
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;"
                        f"border-bottom:1px solid #1E293B;padding:5px 0;"
                        f"font-size:.78rem;'>"
                        f"<span style='color:#94A3B8;'>{nom_d}</span>"
                        f"<span style='color:#E2E8F0;font-weight:700;"
                        f"font-family:monospace;'>{val_d}</span></div>",
                        unsafe_allow_html=True)
        st.divider()

    # ── D) Triage par motif ───────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:.75rem;font-weight:700;color:#64748B;"
        "text-transform:uppercase;'>Triage FRENCH — Motif pédiatrique</div>",
        unsafe_allow_html=True)

    motif_sel = st.selectbox(
        "Motif pédiatrique",
        list(MOTIFS_PED.keys()),
        key="ped_motif_sel")

    det = dict(SS.get("det") or {})
    kw  = dict(
        det=det, age=_age, poids=_poids,
        fc=float(SS.get("v_fc") or 80),
        pas=float(SS.get("v_pas") or 100),
        spo2=float(SS.get("v_spo2") or 98),
        fr=float(SS.get("v_fr") or 20),
        gcs=int(SS.get("v_gcs") or 15),
        temp=float(SS.get("v_temp") or 37.0),
        gl=SS.get("gl"),
        n2=int(SS.get("v_news2") or 0),
    )

    if st.button("⚡ Triage pédiatrique", type="primary",
                 use_container_width=True, key="ped_calc"):
        handler = MOTIFS_PED[motif_sel]
        niv, just, crit = handler(**kw)

        _COLORS = {
            "M":  "#7C3AED", "1": "#DC2626",
            "2":  "#D97706", "3A": "#2563EB",
            "3B": "#0891B2", "4":  "#16A34A", "5": "#475569",
        }
        col = _COLORS.get(niv, "#475569")
        st.markdown(
            f"<div style='background:{col}20;border:3px solid {col};"
            f"border-radius:12px;padding:16px 20px;margin:10px 0;text-align:center;'>"
            f"<div style='font-size:1.5rem;font-weight:900;color:{col};"
            f"font-family:monospace;'>TRI {niv}</div>"
            f"<div style='font-size:.82rem;color:#E2E8F0;margin-top:4px;'>{just}</div>"
            f"<div style='font-size:.7rem;color:#64748B;margin-top:2px;'>{crit}</div>"
            f"</div>",
            unsafe_allow_html=True)

        # Actions immédiates contextuelles
        actions = []
        if niv in ("M", "1"):
            actions += [
                "📞 Appel médecin IMMÉDIAT",
                "📡 Monitorage continu — scope, SpO2, TA",
            ]
        if niv == "1" and "Fièvre" in motif_sel and _age <= 0.25:
            actions.append("🧪 Bilan sepsis : NFS, CRP, hémocultures, ECBU")
        if niv in ("1", "2") and "Épilepsie" in motif_sel:
            actions.append("💊 Midazolam buccal 0.3 mg/kg si crise en cours")
        if niv in ("1", "2") and "Asthme" in motif_sel:
            actions.append("💨 Salbutamol nébulisation 0.15 mg/kg (min 2.5 mg / max 5 mg)")
        if niv == "1" and "Bronchiolite" in motif_sel:
            actions.append("🫁 Position semi-assise — DéSat O2 si < 92%")

        if actions:
            st.markdown(
                "<div style='font-size:.72rem;font-weight:700;color:#64748B;"
                "text-transform:uppercase;margin-top:8px;'>✅ Actions immédiates</div>",
                unsafe_allow_html=True)
            for act in actions:
                st.markdown(f"- {act}")

    st.caption(
        "Sources : SFP/SFMU · SFNP 2023 · GINA 2023 · ESPGHAN 2014 · "
        "HAS 2019 · ATLS 11th — Validation médicale obligatoire.")
