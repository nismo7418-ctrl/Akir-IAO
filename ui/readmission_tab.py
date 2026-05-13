# ui/readmission_tab.py — Onglet Risque de réadmission J30 — AKIR-IAO
# Score LACE (van Walraven 2010) + probabilités empiriques + auto-détection Charlson
from __future__ import annotations

import streamlit as st

from clinical.scores import (
    calculer_lace,
    detecter_charlson_depuis_icd10,
    probabilite_readmission_lace,
)
from clinical.prefill import build_readmission_prefill
from ui.components import H, AL, CARD, DISC
from ui.explainer import explain


_COMORBIDITES_OPTIONS = {
    "Infarctus du myocarde":                "infarctus",
    "Insuffisance cardiaque":               "insuffisance_cardiaque",
    "AVC / AIT":                            "avc",
    "Démence":                              "demence",
    "BPCO / Asthme sévère":                "bpco",
    "Connectivite / PR / LED":              "connectivite",
    "Ulcère peptique":                      "ulcere_peptique",
    "Diabète sans complication":            "diabete_sans_compl",
    "Diabète avec complication":            "diabete_avec_compl",
    "Maladie hépatique légère":             "maladie_hepatique_legere",
    "Maladie hépatique sévère":             "maladie_hepatique_severe",
    "Insuffisance rénale chronique":        "irc_moderee",
    "Hémiplégie":                           "hemiplegie",
    "Tumeur solide sans métastase":         "tumeur_solide",
    "Tumeur métastatique":                  "tumeur_metastatique",
    "Leucémie":                             "leucemie",
    "Lymphome":                             "lymphome",
    "SIDA":                                 "sida",
}

# Inverse lookup : clé Charlson → libellé affiché dans le multiselect
_KEY_TO_LABEL = {v: k for k, v in _COMORBIDITES_OPTIONS.items()}

_DEST_MAP = {
    "Domicile":               "Home",
    "Réhabilitation / SSR":   "Rehab",
    "Maison de repos / Nursing": "Nursing_Facility",
}


def _wk(key: str) -> str:
    SS  = st.session_state
    uid = str(SS.get("uid") or SS.get("sid") or "s")
    return f"{uid}__rdm__{key}"


def _lace_gauge(score: int, couleur: str) -> None:
    pct = min(score / 19 * 100, 100)
    H(f"""
    <div style="margin:12px 0 4px;font-size:.75rem;color:#94A3B8;">
        Score LACE : <strong style="color:{couleur};font-size:1.5rem;">{score}</strong>
        <span style="color:#64748B;"> / 19</span>
    </div>
    <div style="background:#1E293B;border-radius:6px;height:14px;overflow:hidden;">
        <div style="width:{pct:.0f}%;height:100%;background:{couleur};
                    border-radius:6px;transition:width .4s;"></div>
    </div>
    """)


def _composantes_table(comp: dict) -> None:
    rows = [
        ("L — Durée de séjour",            comp["L"], 7),
        ("A — Acuité (urgences)",           comp["A"], 3),
        ("C — Comorbidités (Charlson)",     comp["C"], 5),
        ("E — Passages urgences 6 mois",    comp["E"], 4),
    ]
    html = '<table style="width:100%;border-collapse:collapse;font-size:.82rem;">'
    html += ('<tr style="color:#64748B;">'
             '<th style="text-align:left;padding:4px 8px;">Composante</th>'
             '<th style="text-align:center;">Points</th>'
             '<th style="text-align:center;">Max</th></tr>')
    for label, pts, mx in rows:
        html += (
            f'<tr style="border-top:1px solid #1E293B;">'
            f'<td style="padding:5px 8px;">{label}</td>'
            f'<td style="text-align:center;font-weight:700;color:#E2E8F0;">{pts}</td>'
            f'<td style="text-align:center;color:#64748B;">{mx}</td>'
            f'</tr>'
        )
    html += "</table>"
    H(html)


def _proba_lace_card(score: int) -> None:
    """Affiche la probabilité empirique de réadmission J30 issue de van Walraven 2010."""
    p = probabilite_readmission_lace(score)
    H(f"""
    <div style="background:#0F172A;border:1px solid #1E293B;border-radius:8px;
                padding:12px 16px;margin-top:8px;">
        <div style="font-size:.68rem;color:#64748B;text-transform:uppercase;
                    letter-spacing:.08em;margin-bottom:6px;">
            Probabilité empirique de réadmission J30
        </div>
        <div style="display:flex;align-items:baseline;gap:8px;">
            <span style="font-size:2rem;font-weight:800;color:{p['couleur']};">
                {p['pct']}
            </span>
            <span style="font-size:.85rem;color:{p['couleur']};font-weight:600;">
                {p['risque']}
            </span>
        </div>
        <div style="background:#1E293B;border-radius:4px;height:6px;margin:8px 0;">
            <div style="width:{p['probabilite']*100:.0f}%;height:100%;
                        background:{p['couleur']};border-radius:4px;"></div>
        </div>
        <div style="font-size:.68rem;color:#475569;margin-top:4px;">
            Source : van Walraven C et al., <em>CMAJ</em> 2010;182(6):551-7 —
            cohorte dérivation Ontario (n = 4 812). Ces probabilités sont issues
            du modèle original ; elles peuvent varier selon la population locale.
        </div>
    </div>
    """)


def render() -> None:
    SS = st.session_state

    H('<div style="background:linear-gradient(135deg,#7C3AED,#4F46E5);color:#fff;'
      'border-radius:10px;padding:12px 16px;margin-bottom:14px;">'
      '<div style="font-size:.72rem;opacity:.75;text-transform:uppercase;letter-spacing:.1em;">Post-hospitalisation</div>'
      '<div style="font-size:1rem;font-weight:700;">Risque de réadmission J30</div></div>')

    st.caption("Score LACE · van Walraven C et al., CMAJ 2010;182(6):551-7")

    explain("lace")
    explain("charlson", compact=True)

    # ── Pré-remplissage depuis le profil patient ─────────────────────────────
    _pf = build_readmission_prefill(SS)
    _has_atcd = len(_pf["comorbidites_charlson"]) > 0
    if _has_atcd or _pf.get("urgence_admission"):
        _msg_parts = []
        if _pf.get("urgence_admission"):
            _msg_parts.append(f"admission urgences (Tri {SS.get('niv','?')})")
        if _has_atcd:
            _msg_parts.append(f"{len(_pf['comorbidites_charlson'])} comorbidités Charlson détectées depuis ATCD")
        AL("✓ Pré-rempli : " + " · ".join(_msg_parts), "success")
    if _pf.get("anticoag"):
        AL("⚠️ Anticoagulant détecté — risque hémorragique amplifie le risque de réadmission", "warning")

    # Pré-positionner le multiselect Charlson si pas encore défini par l'IAO
    _comorb_key = _wk("comorbidites")
    if _comorb_key not in SS and _pf["comorbidites_charlson"]:
        SS[_comorb_key] = [
            _KEY_TO_LABEL[k] for k in _pf["comorbidites_charlson"] if k in _KEY_TO_LABEL
        ]

    col_form, col_result = st.columns([1, 1], gap="large")

    with col_form:
        CARD("Paramètres du séjour", "")

        duree = st.number_input(
            "Durée du séjour (jours)",
            min_value=0, max_value=365, value=3, step=1,
            key=_wk("duree"),
        )
        urgence = st.checkbox(
            "Admission via les urgences",
            value=_pf["urgence_admission"],
            key=_wk("urgence"),
            help="Pré-coché si triage M/1/2/3A — modifiable",
        )
        passages = st.slider(
            "Passages aux urgences (6 derniers mois, hors séjour actuel)",
            min_value=0, max_value=4, value=0,
            key=_wk("passages"),
        )

        st.divider()
        CARD("Comorbidités (Index de Charlson)", "")

        # ── Auto-détection ICD-10 ──────────────────────────────────────────
        with st.expander("🔍 Auto-détecter depuis codes ICD-10", expanded=False):
            st.caption(
                "Coller les codes ICD-10 du patient (séparés par virgules ou espaces). "
                "Le système détecte automatiquement les comorbidités Charlson correspondantes."
            )
            icd_raw = st.text_input(
                "Codes ICD-10",
                placeholder="Ex : E11.9, I50, N18.3, C34.1",
                key=_wk("icd10_input"),
            )
            detect_btn = st.button(
                "Détecter Charlson",
                key=_wk("icd10_detect"),
                use_container_width=True,
            )

            if detect_btn and icd_raw:
                # Séparer par virgules, points-virgules ou espaces
                raw_codes = [
                    c.strip()
                    for c in icd_raw.replace(";", ",").replace(" ", ",").split(",")
                    if c.strip()
                ]
                result = detecter_charlson_depuis_icd10(raw_codes)

                # Mettre à jour le multiselect avec les libellés détectés
                detected_labels = [
                    _KEY_TO_LABEL[k]
                    for k in result["comorbidites"]
                    if k in _KEY_TO_LABEL
                ]
                SS[_wk("comorbidites")] = detected_labels
                SS[_wk("icd10_details")] = result

            # Afficher le résultat de la dernière détection
            last = SS.get(_wk("icd10_details"))
            if last:
                if last["details"]:
                    for d in last["details"]:
                        st.success(d, icon="✅")
                if last["non_matches"]:
                    st.caption(
                        f"Codes sans correspondance Charlson : "
                        f"{', '.join(last['non_matches'])}"
                    )

        comorbidites_sel = st.multiselect(
            "Sélectionner les pathologies actives",
            options=list(_COMORBIDITES_OPTIONS.keys()),
            default=[],
            key=_wk("comorbidites"),
            help="Modifiable manuellement après auto-détection ICD-10",
        )
        comorbidites_keys = [_COMORBIDITES_OPTIONS[k] for k in comorbidites_sel]

        st.divider()
        CARD("Destination de sortie", "")
        dest_label = st.selectbox(
            "Orientation à la sortie",
            options=list(_DEST_MAP.keys()),
            key=_wk("destination"),
        )

        calc_btn = st.button(
            "Calculer le risque J30",
            type="primary",
            use_container_width=True,
            key=_wk("calc"),
        )

    with col_result:
        CARD("Résultat — Score LACE", "")

        if calc_btn or SS.get(_wk("lace_done")):
            SS[_wk("lace_done")] = True

            lace = calculer_lace(
                duree_sejour_jours=duree,
                admission_urgence=urgence,
                comorbidites=comorbidites_keys,
                passages_urgences_6mois=passages,
            )

            _lace_gauge(lace["score_total"], lace["couleur"])

            H(f'<div style="background:#0F172A;border-left:4px solid {lace["couleur"]};'
              f'border-radius:0 8px 8px 0;padding:10px 14px;margin:10px 0;">'
              f'<div style="font-size:1rem;font-weight:700;color:{lace["couleur"]};">'
              f'{lace["risque"]}</div>'
              f'<div style="font-size:.82rem;color:#CBD5E1;margin-top:4px;">'
              f'{lace["interpretation"]}</div></div>')

            st.divider()
            CARD("Décomposition L-A-C-E", "")
            _composantes_table(lace["composantes"])

            st.divider()
            CARD("Probabilité de réadmission J30", "")
            _proba_lace_card(lace["score_total"])

            st.divider()
            CARD("Recommandations de sortie", "")
            for rec in lace["recommandations"]:
                st.markdown(f"- {rec}")

        else:
            H('<div style="color:#64748B;text-align:center;padding:40px 0;">'
              '← Renseigner les paramètres et cliquer sur Calculer</div>')

    st.divider()
    DISC()
