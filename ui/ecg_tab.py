"""
ui/ecg_tab.py — Onglet IA ECG AKIR-IAO

Upload d'une image ECG 12 dérivations → classification par CNN
(EfficientNet-B2) → priorité KTAS suggérée + alerte clinique + garde-fous.

Le module fonctionne en mode dégradé si :
  - torch/timm ne sont pas installés (message d'install)
  - le fichier de poids ml/ecg_model.pth n'existe pas (lien vers le script
    d'entraînement)

Aucun appel ML n'est fait tant que l'utilisateur n'a pas cliqué "Analyser".
"""
from __future__ import annotations

import streamlit as st

from ml.ecg_predictor import (
    ECG_LABEL_FR,
    model_available,
    predict_ecg,
)
from ui.components import AL, H
from ui.explainer import explain

_DISCLAIMER = (
    "⚠️ Outil d'aide à la décision — pas un substitut au diagnostic cardiologue. "
    "Toujours confronter à la clinique et obtenir une lecture experte."
)


def render() -> None:
    """Rendu de l'onglet IA ECG."""
    H(
        '<div style="background:linear-gradient(135deg,#7C2D12,#DC2626);color:#fff;'
        'border-radius:10px;padding:12px 16px;margin-bottom:12px;">'
        '<div style="font-size:.72rem;opacity:.8;text-transform:uppercase;letter-spacing:.1em;">'
        'Classification d\'image · 15 diagnostics</div>'
        '<div style="font-size:1rem;font-weight:700;">IA ECG — Analyse de tracé</div></div>'
    )

    explain("ia_ecg", compact=True)

    if not model_available():
        _render_unavailable()
        return

    st.caption(
        "Importez une photo ou scan d'un ECG 12 dérivations standard. "
        "Le modèle classe le tracé parmi 15 diagnostics urgents et suggère "
        "une priorité KTAS."
    )

    uploaded = st.file_uploader(
        "Image ECG (PNG, JPG)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False,
        key="ecg_upload",
        help="Idéalement un ECG complet 12 dérivations, image nette, peu de reflets.",
    )

    if uploaded is None:
        st.info("Aucune image chargée. Importez un ECG pour lancer l'analyse.")
        return

    col_img, col_btn = st.columns([3, 1])
    with col_img:
        st.image(uploaded, caption=uploaded.name, use_container_width=True)
    with col_btn:
        st.markdown("&nbsp;")
        analyze = st.button(
            "🔬 Analyser l'ECG",
            type="primary",
            use_container_width=True,
            key="ecg_analyze",
        )
        st.caption(_DISCLAIMER)

    if not analyze:
        return

    with st.spinner("Inférence ECG en cours…"):
        uploaded.seek(0)
        res = predict_ecg(uploaded.read())

    if res.get("erreur"):
        AL(f"Erreur prédiction ECG : {res['erreur']}", "danger")
        return

    _render_result(res)


def _render_result(res: dict) -> None:
    """Affiche le résultat de la classification + garde-fous + suggestion KTAS."""
    couleur = res["couleur"]
    prio    = res["priorite"]
    label_fr = res["top_label_fr"]
    proba   = res["top_proba"]

    st.markdown(
        f'<div style="background:{couleur};color:white;padding:18px;'
        f'border-radius:10px;text-align:center;font-weight:900;'
        f'box-shadow:0 4px 12px rgba(0,0,0,.2);margin:8px 0;">'
        f'<div style="font-size:1.5rem;">{label_fr}</div>'
        f'<div style="font-size:.85rem;opacity:.9;margin-top:6px;">'
        f'Priorité KTAS suggérée : P{prio} · Confiance ML : {proba:.0%}</div></div>',
        unsafe_allow_html=True,
    )

    alerte = res.get("alerte_clinique")
    if alerte:
        AL(f"🩺 Conduite à tenir : {alerte}", "danger" if prio == 1 else "warning")

    override = res.get("override")
    if override:
        AL(f"⚠️ Ajustement de sécurité appliqué : {override}", "danger")
        prio_ml = res.get("priorite_ml")
        if prio_ml and prio_ml != prio:
            AL(f"Note : la priorité ML initiale était P{prio_ml}.", "info")

    st.divider()
    st.markdown("**📊 Top 5 — autres hypothèses diagnostiques**")
    visible = [(c, l, p) for c, l, p in res["top_k"] if p > 0.0][:5]
    for code, lbl_fr, p in visible:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin:4px 0;">'
            f'<div style="min-width:180px;font-size:.85rem;color:#E2E8F0;">{lbl_fr}</div>'
            f'<div style="flex:1;background:#1E293B;border-radius:6px;height:14px;position:relative;">'
            f'<div style="width:{p*100:.1f}%;background:{couleur};height:100%;border-radius:6px;"></div>'
            f'</div>'
            f'<div style="min-width:50px;text-align:right;font-weight:700;color:#E2E8F0;">{p:.0%}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Avertissement sur les classes non couvertes par ce modèle
    try:
        from ml.ecg_predictor import ECG_LABELS, get_active_labels
        active = set(get_active_labels())
        uncovered = [c for c in ECG_LABELS if c not in active]
        if uncovered:
            from ml.ecg_predictor import ECG_LABEL_FR as _LF
            st.caption(
                f"⚠️ Ce modèle n'a pas été entraîné sur : "
                f"{', '.join(_LF[c] for c in uncovered)}. "
                f"Ne pas s'y fier pour exclure ces diagnostics."
            )
    except Exception:
        pass

    with st.expander("🔬 Analyse de la décision IA"):
        from ui.explainer import render_decision_analysis
        ml_prio = res.get("priorite_ml") or prio
        render_decision_analysis({
            "priorite":    prio,
            "priorite_ml": ml_prio,
            "override":    override,
            "erreur":      None,
        })
        st.caption(
            f"Modèle : {res['features_input'].get('model', '?')} · "
            f"Résolution {res['features_input'].get('resolution', '?')}px · "
            f"{res['features_input'].get('n_classes', '?')} classes"
        )

    st.caption(_DISCLAIMER)


def _render_unavailable() -> None:
    """Affiche le mode dégradé : dépendances manquantes ou poids absents."""
    import importlib.util

    torch_ok = importlib.util.find_spec("torch") is not None
    timm_ok  = importlib.util.find_spec("timm") is not None

    if not torch_ok or not timm_ok:
        manquants = []
        if not torch_ok: manquants.append("torch")
        if not timm_ok:  manquants.append("timm")
        AL(
            f"📦 Dépendances ECG manquantes : `{'`, `'.join(manquants)}`. "
            f"Installer : `pip install {' '.join(manquants)} pillow`",
            "warning",
        )
    else:
        AL(
            "🧠 Modèle ECG non entraîné. Lancer l'entraînement : "
            "`python ml/train_ecg_model.py` (voir le module pour le format de dataset).",
            "info",
        )

    st.markdown("### Labels diagnostiques couverts par le module")
    cols = st.columns(3)
    for i, (code, lbl_fr) in enumerate(ECG_LABEL_FR.items()):
        with cols[i % 3]:
            st.markdown(f"- **{code}** — {lbl_fr}")

    st.caption(_DISCLAIMER)
