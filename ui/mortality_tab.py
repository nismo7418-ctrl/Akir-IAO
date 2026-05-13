# ui/mortality_tab.py — Onglet Mortalité ICU — AKIR-IAO
# Prédiction de risque de mortalité hospitalière (modèle MIMIC-III)
from __future__ import annotations

import streamlit as st

from ui.components import H, AL, CARD, CARD_END
from clinical.prefill import build_mortality_payload
from ui.explainer import explain


def _wk(key: str) -> str:
    SS  = st.session_state
    uid = str(SS.get("uid") or SS.get("sid") or "s")
    return f"{uid}__mort__{key}"


def _gauge_mortality(proba: float, couleur: str) -> None:
    pct = min(proba * 100, 100)
    H(f"""
    <div style="margin:12px 0 4px;">
      <div style="font-size:.75rem;color:#94A3B8;margin-bottom:4px;">
        Probabilité de mortalité hospitalière
      </div>
      <div style="font-size:2.2rem;font-weight:800;color:{couleur};line-height:1;">
        {pct:.1f}%
      </div>
      <div style="background:#1E293B;border-radius:6px;height:18px;overflow:hidden;margin-top:6px;">
        <div style="width:{pct:.1f}%;height:100%;background:{couleur};
                    transition:width .4s ease;border-radius:6px;"></div>
      </div>
    </div>
    """)


def _sofa_bar(score: float) -> None:
    max_sofa = 24
    pct = min(score / max_sofa * 100, 100)
    color = "#EF4444" if score >= 10 else "#F97316" if score >= 6 else "#EAB308" if score >= 3 else "#22C55E"
    H(f"""
    <div style="margin:8px 0;">
      <div style="font-size:.72rem;color:#94A3B8;margin-bottom:3px;">
        Score SOFA proxy (estimation) : <strong style="color:{color}">{score:.0f}</strong> / 24
      </div>
      <div style="background:#1E293B;border-radius:4px;height:8px;overflow:hidden;">
        <div style="width:{pct:.1f}%;height:100%;background:{color};border-radius:4px;"></div>
      </div>
    </div>
    """)


def _prefill_from_session() -> dict:
    """Pré-remplit depuis le contexte clinique courant.

    Utilise le helper centralisé build_mortality_payload qui agrège les vitaux
    actuels + l'historique des réévaluations pour calculer mean/min/max.
    """
    return build_mortality_payload(st.session_state)


def render() -> None:
    SS = st.session_state

    H('<div style="background:linear-gradient(135deg,#7C3AED,#4F46E5);color:#fff;'
      'border-radius:10px;padding:12px 16px;margin-bottom:12px;">'
      '<div style="font-size:.72rem;opacity:.75;text-transform:uppercase;letter-spacing:.1em;">'
      'MIMIC-III · Données réelles ICU</div>'
      '<div style="font-size:1rem;font-weight:700;">Prédiction Mortalité Hospitalière</div>'
      '</div>')

    AL("Ce modèle est entraîné sur des données ICU réelles (MIMIC-III, MIT). "
       "Il évalue le risque de décès hospitalier à partir des paramètres vitaux. "
       "Indicatif — ne se substitue pas au jugement clinique.", "warning")

    explain("ia_mortalite")
    explain("mimic", compact=True)
    explain("sofa_proxy", compact=True)

    pf = _prefill_from_session()
    SS = st.session_state
    _has_reev = len(SS.get("reevs") or []) >= 3

    if _has_reev:
        AL(f"✓ Agrégats calculés depuis {len(SS.reevs)} réévaluations + vitaux courants.", "success")
    else:
        AL("ℹ️ Pas assez de réévaluations — min/max estimés ± variation physiologique.", "info")

    # ── Saisie vitaux ─────────────────────────────────────────────────────────
    with st.expander("Paramètres vitaux (valeurs de séjour)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            hr_mean  = st.number_input("FC moyenne (bpm)",  min_value=20,  max_value=300, value=int(pf["hr_mean"]),   step=1,  key=_wk("hr_mean"))
            hr_min   = st.number_input("FC min (bpm)",       min_value=20,  max_value=300, value=int(pf["hr_min"]),   step=1, key=_wk("hr_min"))
            hr_max   = st.number_input("FC max (bpm)",       min_value=20,  max_value=300, value=int(pf["hr_max"]),   step=1, key=_wk("hr_max"))
        with c2:
            sbp_mean = st.number_input("PAS moyenne (mmHg)", min_value=40,  max_value=300, value=int(pf["sbp_mean"]), step=1,  key=_wk("sbp_mean"))
            sbp_min  = st.number_input("PAS min (mmHg)",     min_value=40,  max_value=300, value=int(pf["sbp_min"]),  step=1, key=_wk("sbp_min"))
            dbp_mean = st.number_input("PAD moyenne (mmHg)", min_value=10,  max_value=200, value=int(pf["dbp_mean"]), step=1,  key=_wk("dbp_mean"))
        with c3:
            spo2_mean = st.number_input("SpO2 moyenne (%)",  min_value=50,  max_value=100, value=int(pf["spo2_mean"]), step=1,  key=_wk("spo2_mean"))
            spo2_min  = st.number_input("SpO2 min (%)",      min_value=50,  max_value=100, value=int(pf["spo2_min"]),  step=1, key=_wk("spo2_min"))
            rr_mean   = st.number_input("FR moyenne (/min)", min_value=4,   max_value=60,  value=int(pf["rr_mean"]),   step=1,  key=_wk("rr_mean"))
            rr_max    = st.number_input("FR max (/min)",     min_value=4,   max_value=60,  value=int(pf["rr_max"]),    step=1, key=_wk("rr_max"))

    with st.expander("Démographie & contexte admission", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            age        = st.number_input("Âge (ans)", min_value=18, max_value=120, value=int(pf["age_approx"]), key=_wk("age"))
            _gender_default = "Femme" if pf["gender_enc"] == 1 else "Homme"
            gender     = st.selectbox("Genre", ["Homme", "Femme"], index=(1 if _gender_default == "Femme" else 0), key=_wk("gender"))
            gender_enc = 1 if gender == "Femme" else 0
        with c2:
            temp_mean  = st.number_input("Temp. moyenne (°C)", min_value=30.0, max_value=45.0, value=float(pf["temp_c_mean"]), step=0.1, format="%.1f", key=_wk("temp_mean"))
            temp_max   = st.number_input("Temp. max (°C)",     min_value=30.0, max_value=45.0, value=float(pf["temp_c_max"]),  step=0.1, format="%.1f", key=_wk("temp_max"))
        with c3:
            _adm_lbls  = ["Électif", "Urgent", "Urgences"]
            _adm_idx   = int(pf["admission_type_enc"])
            adm_type   = st.selectbox("Type admission", _adm_lbls, index=_adm_idx, key=_wk("adm_type"))
            adm_enc    = _adm_lbls.index(adm_type)
            los_h      = st.number_input("Durée séjour (heures)", min_value=0, max_value=5000, value=int(pf["los_hours"]), key=_wk("los_h"))
            n_mesures  = st.number_input("Nb mesures vitaux", min_value=0, max_value=10000, value=int(pf["n_vital_measures"]), key=_wk("n_mesures"),
                                          help="Nombre total de mesures enregistrées — proxy de l'intensité du monitoring.")

    # ── Prédiction ────────────────────────────────────────────────────────────
    if st.button("Calculer le risque de mortalité", type="primary", use_container_width=True, key=_wk("btn")):
        try:
            from ml.mortality_predictor import predict_mortality
        except ImportError as e:
            AL(f"Module ML non disponible : {e}", "error")
            return

        map_mean = (sbp_mean + 2 * dbp_mean) / 3
        map_min  = (sbp_min  + 2 * dbp_mean) / 3
        si       = hr_mean / sbp_mean if sbp_mean > 0 else 1.0

        payload = {
            "hr_mean":          hr_mean,  "hr_min":   hr_min,  "hr_max":   hr_max,
            "spo2_mean":        spo2_mean, "spo2_min": spo2_min,
            "rr_mean":          rr_mean,  "rr_max":   rr_max,
            "sbp_mean":         sbp_mean, "sbp_min":  sbp_min,
            "dbp_mean":         dbp_mean,
            "map_mean":         map_mean, "map_min":  map_min,
            "temp_c_mean":      temp_mean, "temp_c_max": temp_max,
            "shock_index":      si,
            "los_hours":        los_h,
            "admission_type_enc": adm_enc,
            "gender_enc":       gender_enc,
            "age_approx":       age,
            "n_vital_measures": n_mesures,
        }

        res = predict_mortality(payload)

        if res["erreur"]:
            AL(f"Erreur prédiction : {res['erreur']}", "error")
            return

        # ── Affichage résultat ─────────────────────────────────────────────
        H(CARD)
        col_r, col_d = st.columns([1, 1])

        with col_r:
            H(f'<div style="font-size:2.4rem;text-align:center;">{res["icone"]}</div>')
            H(f'<div style="text-align:center;font-size:1.1rem;font-weight:700;color:{res["couleur"]};">'
              f'{res["risque"]}</div>')
            _gauge_mortality(res["probabilite"], res["couleur"])
            if res["score_sofa_proxy"] is not None:
                _sofa_bar(res["score_sofa_proxy"])

        with col_d:
            si_val = round(si, 2)
            si_color = "#EF4444" if si_val > 1.0 else "#F97316" if si_val > 0.8 else "#22C55E"
            H(f"""
            <div style="font-size:.75rem;color:#94A3B8;margin-bottom:8px;">Indicateurs dérivés</div>
            <div style="display:flex;flex-direction:column;gap:6px;">
              <div style="background:#1E293B;padding:8px 12px;border-radius:8px;">
                <span style="color:#94A3B8;font-size:.7rem;">Index de choc</span><br>
                <span style="font-size:1.2rem;font-weight:700;color:{si_color};">{si_val:.2f}</span>
                <span style="color:#64748B;font-size:.7rem;"> (norm < 0.9)</span>
              </div>
              <div style="background:#1E293B;padding:8px 12px;border-radius:8px;">
                <span style="color:#94A3B8;font-size:.7rem;">PAM moyenne</span><br>
                <span style="font-size:1.2rem;font-weight:700;
                  color:{'#EF4444' if map_mean < 65 else '#22C55E'};">{map_mean:.0f} mmHg</span>
              </div>
              <div style="background:#1E293B;padding:8px 12px;border-radius:8px;">
                <span style="color:#94A3B8;font-size:.7rem;">SpO2 min</span><br>
                <span style="font-size:1.2rem;font-weight:700;
                  color:{'#EF4444' if spo2_min < 90 else '#F97316' if spo2_min < 95 else '#22C55E'};">{spo2_min}%</span>
              </div>
            </div>
            """)

        H(CARD_END)

        # ── Facteurs d'alarme ──────────────────────────────────────────────
        if res["facteurs_alarme"]:
            H('<div style="margin-top:12px;">')
            H('<div style="font-size:.75rem;font-weight:600;color:#F97316;margin-bottom:6px;">Signes de gravité détectés</div>')
            for alm in res["facteurs_alarme"]:
                AL(alm, "warning")
            H('</div>')
        else:
            AL("Aucun signe d'alarme majeur détecté sur les paramètres saisis.", "info")

        # ── Recommandations contextuelles ──────────────────────────────────
        proba = res["probabilite"]
        H('<div style="margin-top:12px;background:#1E293B;padding:12px;border-radius:8px;">')
        H('<div style="font-size:.75rem;font-weight:600;color:#94A3B8;margin-bottom:8px;">Recommandations</div>')
        if proba >= 0.60:
            recs = [
                "Activation du staff médical senior immédiate",
                "Réévaluation SOFA complète (biologie + hémodynamique)",
                "Discussion précoce objectifs de soins / réanimation",
                "Surveillance continue FC, PAM, SpO2, diurèse",
            ]
        elif proba >= 0.35:
            recs = [
                "Surveillance rapprochée toutes les 2h",
                "Bilan biologique complet (lactates, NFS, BH, TP)",
                "Réévaluation hémodynamique — écho cardiaque si disponible",
            ]
        elif proba >= 0.15:
            recs = [
                "Monitoring standard — réévaluation toutes les 4-6h",
                "Optimisation volémique et analgésie",
            ]
        else:
            recs = [
                "Suivi standard de soins intensifs",
                "Réévaluation quotidienne du score SOFA",
            ]
        for r in recs:
            H(f'<div style="font-size:.72rem;color:#CBD5E1;padding:3px 0;'
              f'border-left:3px solid #4F46E5;padding-left:8px;margin-bottom:4px;">{r}</div>')
        H('</div>')

    else:
        # État initial
        H('<div style="text-align:center;padding:32px;color:#475569;">'
          '<div style="font-size:2rem;margin-bottom:8px;">🏥</div>'
          '<div style="font-size:.85rem;">Renseignez les paramètres vitaux puis lancez la prédiction.</div>'
          '<div style="font-size:.75rem;margin-top:6px;color:#334155;">'
          'Modèle entraîné sur 70+ séjours ICU réels — MIMIC-III (MIT)</div>'
          '</div>')

    # ── Source des données ─────────────────────────────────────────────────
    with st.expander("À propos du modèle", expanded=False):
        st.markdown("""
**Données d'entraînement** : MIMIC-III (Medical Information Mart for Intensive Care, MIT)
- 70 séjours ICU avec paramètres vitaux réels (758 355 mesures)
- 100 patients, taux de mortalité 31%
- Vitaux agrégés par séjour : FC, SpO2, FR, PA, PAM, Température, PVC

**Algorithme** : Ensemble soft-voting (GradientBoosting + RandomForest + LogisticRegression)

**Features** : 20 variables — vitaux agrégés (mean/min/max) + démographie + contexte admission

**Performances** (CV-5) : AUC-ROC ≈ 0.78–0.85 selon la partition

**Limites** :
- Dataset de taille modeste (70 séjours avec vitaux)
- Patients MIMIC-III (centre tertiaire US) — peut ne pas représenter ta population
- Score SOFA proxy : estimation partielle (pas de biologie disponible)
        """)
