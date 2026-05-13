"""
ui/explainer.py — Composant d'aide pédagogique contextuelle.

Affiche des explications cliniques accessibles aux utilisateurs non-experts
(étudiants infirmiers, nouveaux IAO, médecins non-urgentistes, curieux).

Usage :
    from ui.explainer import explain, glossary_grid

    explain("news2")              # Expander compact "ℹ️ Comprendre NEWS2"
    explain("news2", inline=True) # Chip cliquable + popover (mobile)
    glossary_grid()               # Grille complète de tous les termes
"""
from __future__ import annotations

import streamlit as st

from clinical.glossary import get, keys


def explain(key: str, *, label: str | None = None, compact: bool = False) -> None:
    """Affiche un expander discret avec l'explication d'un terme.

    Args:
        key: clé du glossaire (ex. "news2", "qsofa")
        label: surcharge du titre (par défaut : "ℹ️ Comprendre {title}")
        compact: si True, affiche uniquement le tldr (1 phrase)
    """
    entry = get(key)
    if entry is None:
        return

    title = entry.get("title", key)
    tldr  = entry.get("tldr", "")
    body  = entry.get("body", "")
    source = entry.get("source", "")

    display = label or f"ℹ️ Comprendre — {title}"

    with st.expander(display, expanded=False):
        if compact:
            st.markdown(f"*{tldr}*")
        else:
            if tldr:
                st.markdown(f"**{tldr}**")
            if body:
                st.markdown(body)
            if source:
                st.caption(f"📚 Source : {source}")


def explain_inline(key: str, *, prefix: str = "💡 ") -> None:
    """Variante très compacte : juste 1 ligne en italique avec le tldr."""
    entry = get(key)
    if entry is None:
        return
    st.caption(f"{prefix}_{entry.get('tldr', '')}_")


def glossary_grid() -> None:
    """Affiche la grille complète du glossaire — utile pour une page Aide.

    Groupe les entrées par catégorie thématique.
    """
    categories: dict[str, list[str]] = {
        "🩺 Scores cliniques": [
            "news2", "pews", "qsofa", "gcs", "avpu", "shock_index",
            "lace", "charlson", "heart", "nihss", "ciwa", "wells", "perc",
        ],
        "⚡ Triage & workflow": [
            "french", "sbar", "5b", "next_action", "audit_log",
        ],
        "🤖 Intelligence artificielle": [
            "ia_triage", "ia_mortalite", "ia_readmission",
            "mimic", "ktas", "sofa_proxy",
        ],
        "💊 Pharmacologie & outils": [
            "rsi", "broselow", "code_stroke", "dfge", "aod",
            "bpco_spo2", "poids_ideal", "sepsis_bundle",
        ],
        "📚 Référentiels": [
            "icd10",
        ],
    }

    st.markdown(
        '<div style="background:linear-gradient(135deg,#0F766E,#2563EB);'
        'color:#fff;border-radius:10px;padding:12px 16px;margin-bottom:14px;">'
        '<div style="font-size:.72rem;opacity:.75;text-transform:uppercase;letter-spacing:.1em;">'
        'Aide pédagogique</div>'
        '<div style="font-size:1.1rem;font-weight:800;">Glossaire des outils cliniques</div>'
        '<div style="font-size:.78rem;opacity:.85;margin-top:4px;">'
        'Explications accessibles — pour étudiants, nouveaux IAO, curieux médicaux.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Filtre de recherche
    query = st.text_input(
        "🔍 Rechercher un terme",
        placeholder="ex: NEWS2, sepsis, shock...",
        key="glossary_search",
    )
    q_norm = (query or "").lower().strip()

    found_any = False
    for cat_label, cat_keys in categories.items():
        # Filtrer par recherche
        if q_norm:
            cat_keys = [k for k in cat_keys
                        if q_norm in k
                        or q_norm in (get(k) or {}).get("title", "").lower()
                        or q_norm in (get(k) or {}).get("tldr", "").lower()]
        if not cat_keys:
            continue
        found_any = True

        st.markdown(f"### {cat_label}")
        for k in cat_keys:
            entry = get(k)
            if entry is None:
                continue
            with st.expander(f"**{entry['title']}**"):
                st.markdown(f"**TL;DR** — {entry['tldr']}")
                st.markdown(entry['body'])
                st.caption(f"📚 {entry['source']}")

    if q_norm and not found_any:
        st.info(f"Aucun terme trouvé pour « {query} ». Essayez une autre recherche.")


def info_chip(key: str) -> None:
    """Affiche un petit chip cliquable qui révèle l'explication au tap.

    Utilise un détails/summary HTML natif (pas de Streamlit re-run).
    Plus léger qu'un expander pour les zones denses.
    """
    entry = get(key)
    if entry is None:
        return
    title = entry["title"]
    tldr  = entry["tldr"]
    body  = entry["body"]
    src   = entry["source"]

    st.markdown(
        f"""
<details class="akir-info-chip">
  <summary>ℹ️ {title}</summary>
  <div class="akir-info-body">
    <p><strong>{tldr}</strong></p>
    <p>{body}</p>
    <p class="akir-info-source">📚 {src}</p>
  </div>
</details>
        """,
        unsafe_allow_html=True,
    )
