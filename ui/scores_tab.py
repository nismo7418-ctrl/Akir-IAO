# ui/scores_tab.py — Onglet Scores cliniques — AKIR-IAO v20
# Logique extraite de streamlit_app.py T[3] (modularisation)
from __future__ import annotations
import streamlit as st
from datetime import datetime

from clinical.scores import (
    calculer_qsofa, calculer_heart, calculer_timi, evaluer_fast,
    calculer_algoplus, calculer_wells_tvp, calculer_wells_ep,
    calculer_sofa_partiel, calculer_curb65,
    regle_ottawa_cheville, regle_canadian_ct,
    calculer_abcd2, calculer_perc, calculer_grace,
    calculer_ciwa, calculer_pews,
    calculer_nihss_rapide, calculer_pram,
    calculer_croup, poids_estime_enfant,
    surface_corporelle_mosteller, terme_naegele,
    calculer_pss, identifier_toxidrome, evaluer_paracetamol_intox,
    evaluer_tricycliques_ecg, calculer_toxic2,
    TOXIDROMES, PSS_CRITERES,
)
from akir_iao_enhancements import sync_clinical_context
from ui.components import H, AL, CARD, CARD_END
from ui.explainer import explain


def _wk(base: str, scope: str | None = None) -> str:
    SS = st.session_state
    parts = [str(SS.get("uid") or SS.get("sid") or "s")]
    if scope:
        parts.append(str(scope))
    parts.append(str(base))
    return "__".join(p.replace(" ", "_") for p in parts if p)


def _render_nihss_rapide(WK) -> None:
    CARD("NIHSS rapide — Déficit neurologique AVC (5 items)", "")
    st.caption("Schiemanck SK et al., Cerebrovasc Dis 2006 | r = 0,89 avec NIHSS complet")
    AL("Score ≥ 1 + délai < 4,5h → évaluer thrombolyse — Code Stroke immédiat", "warning")
    _nh1, _nh2 = st.columns(2)
    _ni_cons = _nh1.select_slider(
        "Conscience (0-3)",
        options=[0,1,2,3],
        format_func=lambda x:{0:"0–Normal",1:"1–Somnolent",2:"2–Stuporeux",3:"3–Coma"}[x],
        key=WK("ni_cons"))
    _ni_reg  = _nh2.checkbox("Déviation conjuguée du regard", key=WK("ni_reg"))
    _ni_fac  = _nh1.select_slider(
        "Paralysie faciale (0-3)",
        options=[0,1,2,3],
        format_func=lambda x:{0:"0–Normal",1:"1–Légère",2:"2–Partielle",3:"3–Complète"}[x],
        key=WK("ni_fac"))
    _ni_mot  = _nh2.select_slider(
        "Moteur bras (0-4)",
        options=[0,1,2,3,4],
        format_func=lambda x:{0:"0–Normal",1:"1–Dérive",2:"2–↓Gravité",3:"3–Aucun mvt",4:"4–Plégie"}[x],
        key=WK("ni_mot"))
    _ni_lan  = _nh1.select_slider(
        "Langage (0-3)",
        options=[0,1,2,3],
        format_func=lambda x:{0:"0–Normal",1:"1–Aphasie légère",2:"2–Aphasie sévère",3:"3–Muet"}[x],
        key=WK("ni_lan"))
    _ni_res = calculer_nihss_rapide(
        int(_ni_cons), bool(_ni_reg), int(_ni_fac), int(_ni_mot), int(_ni_lan))
    _ni_v = _ni_res.get("score_val") or 0
    _ni_col = "#EF4444" if _ni_v >= 16 else "#F59E0B" if _ni_v >= 5 else "#22C55E"
    H(f'<div style="background:#0F172A;border-radius:8px;padding:12px;display:flex;'
      f'align-items:center;gap:16px;margin:8px 0;">'
      f'<div style="text-align:center;min-width:80px;">'
      f'<div style="font-size:.72rem;color:#64748B;">NIHSS</div>'
      f'<div style="font-size:2.2rem;font-weight:900;color:{_ni_col};">{_ni_v}/18</div></div>'
      f'<div style="font-size:.78rem;color:#94A3B8;flex:1;">{_ni_res.get("interpretation","")}</div></div>')
    AL(_ni_res.get("recommendation",""), "danger" if _ni_v >= 16 else "warning" if _ni_v >= 5 else "info")
    CARD_END()


def render() -> None:
    SS = st.session_state
    WK = _wk

    age    = float(SS.get("age") or 45)
    poids  = float(SS.get("poids") or 70)
    taille = float(SS.get("taille") or 170)

    _smart = sync_clinical_context(SS)
    _nihss_priority = _smart.get("focus_score") == "nihss"
    if _nihss_priority:
        H('<div class="smart-tab-note">🧠 Déficit focal/AVC détecté — NIHSS rapide affiché en priorité.</div>')
        _render_nihss_rapide(WK)
        st.divider()
    elif age >= 18:
        H('<div class="smart-tab-note muted">▫️ Patient adulte — les outils pédiatriques sont mis en retrait.</div>')

    _labels = ["Cardio / Neuro", "Infectio / Respi", "Imagerie", "Neuro Spéc.", "Pédia / Sevrage", "☠️ Toxicologie"]
    if _nihss_priority:
        _labels[3] = "🧠 NIHSS / Neuro"
    if age >= 18:
        _labels[4] = "▫️ Pédia"
    _SC = st.tabs(_labels)

    # ── SC[0] CARDIO / NEURO ─────────────────────────────────────────────────
    with _SC[0]:
        with st.expander("ℹ️ Comprendre les scores Cardio / Neuro", expanded=False):
            _ec1, _ec2 = st.columns(2)
            with _ec1:
                explain("qsofa")
                explain("heart")
                explain("timi")
            with _ec2:
                explain("grace")
                explain("nihss")
        _sl, _sr = st.columns(2)
        with _sl:
            CARD("qSOFA — Sepsis", "")
            _qs = calculer_qsofa(SS.v_fr or 16, SS.v_gcs or 15, SS.v_pas or 120)
            _qsv = _qs.get("score_val") or 0
            AL(_qs.get("interpretation",""), "danger" if _qsv >= 2 else "warning" if _qsv == 1 else "success")
            AL(_qs.get("recommendation",""), "info")
            CARD_END()

            CARD("BE-FAST — AVC", "")
            _f1, _f2 = st.columns(2)
            _bf_ba = _f1.checkbox("Balance", key=WK("bf_b"))
            _bf_ey = _f2.checkbox("Eyes",    key=WK("bf_e"))
            _bf_fa = _f1.checkbox("Face",    key=WK("bf_f"))
            _bf_ar = _f2.checkbox("Arm",     key=WK("bf_a"))
            _bf_sp = _f1.checkbox("Speech",  key=WK("bf_sp"))
            _bf_ti = _f2.text_input("Vu bien à", key="bf_t", placeholder="14:30")
            _bf = evaluer_fast(_bf_fa, _bf_ar, _bf_sp, _bf_ti, _bf_ba, _bf_ey)
            AL(_bf.get("interpretation",""), "danger" if (_bf.get("score_val") or 0) >= 1 else "success")
            AL(_bf.get("recommendation",""), "info")
            CARD_END()

        with _sr:
            CARD("HEART — Douleur thoracique", "")
            st.caption("Six AJ et al., NHJ 2008")
            _h1, _h2 = st.columns(2)
            _hh = _h1.select_slider("Histoire", [0,1,2], key=WK("ht_h"),
                format_func=lambda x:{0:"0–Peu évoc.",1:"1–Modéré",2:"2–Très suspect"}[x])
            _he = _h2.select_slider("ECG",     [0,1,2], key=WK("ht_e"),
                format_func=lambda x:{0:"0–Normal",1:"1–Non spéc.",2:"2–Bloc/STEMI"}[x])
            _ha = _h1.select_slider("Âge",     [0,1,2], key=WK("ht_a"),
                format_func=lambda x:{0:"0–<45",1:"1–45-65",2:"2–>65"}[x])
            _hr = _h2.select_slider("FRCV",    [0,1,2], key=WK("ht_r"),
                format_func=lambda x:{0:"0–Aucun",1:"1–1-2",2:"2–≥3"}[x])
            _ht2 = _h1.select_slider("Tropo",  [0,1,2], key=WK("ht_t"),
                format_func=lambda x:{0:"0–Norm.",1:"1–1-3xN",2:"2–>3xN"}[x])
            _ht = calculer_heart(_hh, _he, _ha, _hr, _ht2)
            _htv = _ht.get("score_val") or 0
            AL(_ht.get("interpretation",""), "danger" if _htv >= 7 else "warning" if _htv >= 4 else "success")
            AL(_ht.get("recommendation",""), "info")
            CARD_END()

            if any(k in (SS.motif or "").lower() for k in ("thoracique","sca","coronaire","infarctus")):
                CARD("TIMI — NSTEMI (motif SCA actif)", "")
                st.caption("Antman EM et al., JAMA 2000")
                _ti1, _ti2 = st.columns(2)
                _tia = _ti1.checkbox("Âge ≥ 65 ans",   key=WK("ti_age"), value=age >= 65)
                _tif = _ti2.checkbox("≥ 3 FRCV",        key=WK("ti_frcv"))
                _tis = _ti1.checkbox("Sténose ≥ 50 %",  key=WK("ti_sten"))
                _tie = _ti2.checkbox("Dév. ST ECG",      key=WK("ti_ecg"))
                _tin = _ti1.checkbox("≥ 2 angor/24h",   key=WK("ti_ang"))
                _tiasp = _ti2.checkbox("Aspirine 7j",   key=WK("ti_asp"))
                _titr = _ti1.checkbox("Marqueurs +",    key=WK("ti_trop"))
                _tires = calculer_timi(_tia, _tif, _tis, _tie, _tin, _tiasp, _titr)
                _tisv  = _tires.get("score_val") or 0
                _ticol = "#EF4444" if _tisv >= 5 else "#F59E0B" if _tisv >= 3 else "#22C55E"
                H(f'<div style="background:#1E293B;border-radius:8px;padding:12px;text-align:center;margin:8px 0;">'
                  f'<div style="font-size:.72rem;color:#64748B;text-transform:uppercase;">TIMI</div>'
                  f'<div style="font-size:2.2rem;font-weight:900;color:{_ticol};">{_tisv}/7</div>'
                  f'<div style="font-size:.72rem;color:#94A3B8;">{_tires.get("interpretation","")}</div>'
                  f'</div>')
                AL(_tires.get("recommendation",""), "danger" if _tisv >= 5 else "warning" if _tisv >= 3 else "info")
                CARD_END()

            CARD("Algoplus — Non communicant", "")
            _al1, _al2 = st.columns(2)
            _alv = _al1.checkbox("Visage",       key=WK("alg_v"))
            _alr = _al2.checkbox("Regard",       key=WK("alg_r"))
            _alp = _al1.checkbox("Plaintes",     key=WK("alg_p"))
            _ala = _al2.checkbox("Attitudes",    key=WK("alg_a"))
            _alc = _al1.checkbox("Comportement", key=WK("alg_c"))
            _alres = calculer_algoplus(_alv, _alr, _alp, _ala, _alc)
            AL(_alres.get("interpretation",""),
               "danger" if (_alres.get("score_val") or 0) >= 2 else "success")
            AL(_alres.get("recommendation",""), "info")
            CARD_END()

    # ── SC[1] INFECTIO / RESPI ───────────────────────────────────────────────
    with _SC[1]:
        with st.expander("ℹ️ Comprendre les scores Infectio / Respi", expanded=False):
            _e1, _e2 = st.columns(2)
            with _e1:
                explain("curb65")
                explain("wells_ep")
            with _e2:
                explain("perc")
                explain("sepsis_bundle")
        _s2l, _s2r = st.columns(2)
        with _s2l:
            CARD("CURB-65 — Pneumonie", "")
            _cbc = st.checkbox("Confusion",         key=WK("cb_c"))
            _cbu = st.checkbox("Urée > 7 mmol/l",  key=WK("cb_u"))
            _cbr = st.checkbox("FR ≥ 30/min",      key=WK("cb_r"), value=(SS.v_fr or 16) >= 30)
            _cbb = st.checkbox("PAS < 90",          key=WK("cb_b"), value=(SS.v_pas or 120) < 90)
            _cba = st.checkbox("Âge ≥ 65",          key=WK("cb_a"), value=age >= 65)
            _cbres = calculer_curb65(_cbc, _cbu, _cbr, _cbb, _cba)
            AL(_cbres.get("interpretation",""), "danger" if (_cbres.get("score_val") or 0) >= 3 else
               "warning" if (_cbres.get("score_val") or 0) == 2 else "success")
            AL(_cbres.get("recommendation",""), "info")
            CARD_END()

        with _s2r:
            CARD("Wells EP", "")
            _we1, _we2 = st.columns(2)
            _wetvp = _we1.checkbox("Symptômes TVP",   key=WK("we_tvp"))
            _weep  = _we2.checkbox("EP probable",     key=WK("we_ep"))
            _wefc  = _we1.checkbox("FC > 100",        key=WK("we_fc"), value=(SS.v_fc or 80) > 100)
            _weim  = _we2.checkbox("Immobilisation",  key=WK("we_im"))
            _wean  = _we1.checkbox("ATCD TVP/EP",     key=WK("we_an"))
            _wehe  = _we2.checkbox("Hémoptysie",      key=WK("we_he"))
            _weca  = _we1.checkbox("Cancer",          key=WK("we_ca"))
            _weres = calculer_wells_ep(_wetvp, _weep, _wefc, _weim, _wean, _wehe, _weca)
            AL(_weres.get("interpretation",""), "danger" if (_weres.get("score_val") or 0) > 4 else
               "warning" if (_weres.get("score_val") or 0) > 1 else "success")
            AL(_weres.get("recommendation",""), "info")
            CARD_END()

    # ── SC[2] IMAGERIE ───────────────────────────────────────────────────────
    with _SC[2]:
        with st.expander("ℹ️ Comprendre les règles d'imagerie", expanded=False):
            _e1, _e2 = st.columns(2)
            with _e1:
                explain("ottawa")
                explain("canadian_ct")
            with _e2:
                explain("fast")
                explain("wells")
        _s3l, _s3r = st.columns(2)
        with _s3l:
            CARD("Ottawa — Cheville / Pied", "")
            _otap = st.checkbox("Incapacité d'appui (4 pas)", key=WK("ot_ap"))
            _ot1, _ot2 = st.columns(2)
            _otmm = _ot1.checkbox("Malléole médiale",  key=WK("ot_mm"))
            _ottl = _ot2.checkbox("Malléole latérale", key=WK("ot_tl"))
            _ot5m = _ot1.checkbox("Base 5e métatar.", key=WK("ot_5m"))
            _otnv = _ot2.checkbox("Naviculaire",       key=WK("ot_nv"))
            _otres = regle_ottawa_cheville(_otmm, _ottl, _ot5m, _otnv, _otap)
            AL(_otres.get("interpretation",""), "warning" if _otres.get("score_val") else "success")
            AL(_otres.get("recommendation",""), "info")
            CARD_END()
        with _s3r:
            CARD("Canadienne — TDM crânien (GCS 13-15)", "")
            _cc1, _cc2 = st.columns(2)
            _ccg  = _cc1.checkbox("GCS < 15 à 2h",        key=WK("cc_g"))
            _ccs  = _cc2.checkbox("Fracture ouverte",      key=WK("cc_s"))
            _ccf  = _cc1.checkbox("Fracture base crâne",   key=WK("cc_f"))
            _ccv  = _cc2.checkbox("Vomissements ≥ 2",     key=WK("cc_v"))
            _cca  = _cc1.checkbox("Âge ≥ 65",             key=WK("cc_a"), value=age >= 65)
            _ccam = _cc2.checkbox("Amnésie ≥ 30 min",     key=WK("cc_am"))
            _ccm  = _cc1.checkbox("Mécanisme dangereux",   key=WK("cc_m"))
            _ccres = regle_canadian_ct(_ccg, _ccs, _ccf, _ccv, _cca, _ccam, _ccm)
            AL(_ccres.get("interpretation",""), "danger" if (_ccres.get("score_val") or 0) == 2 else
               "warning" if (_ccres.get("score_val") or 0) == 1 else "success")
            AL(_ccres.get("recommendation",""), "info")
            CARD_END()

    # ── SC[3] NEURO SPÉCIALISÉS ──────────────────────────────────────────────
    with _SC[3]:
        with st.expander("ℹ️ Comprendre les scores Neurologie spécifiques", expanded=False):
            _e1, _e2 = st.columns(2)
            with _e1:
                explain("nihss")
                explain("nihss_rapide")
                explain("abcd2")
            with _e2:
                explain("gcs")
                explain("avpu")
                explain("cam_icu")
        _n1, _n2c = st.columns(2)
        with _n1:
            CARD("ABCD2 — Risque AVC après AIT", "")
            st.caption("Johnston SC et al., Lancet 2007")
            AL("Applicable après tout déficit neurologique transitoire", "info")
            _ab1, _ab2 = st.columns(2)
            _ab_age  = _ab1.checkbox("Âge ≥ 60 ans", key=WK("ab_age"), value=age >= 60)
            _ab_hta  = _ab2.checkbox("HTA / PAS ≥ 140", key=WK("ab_hta"))
            _ab_diab = _ab1.checkbox("Diabète", key=WK("ab_diab"))
            _ab_type = st.radio("Symptôme dominant",
                ["autre", "trouble_parole", "hemiplegie"],
                format_func=lambda x: {"autre":"Autre","trouble_parole":"Trouble parole","hemiplegie":"Hémiplégie"}[x],
                horizontal=True, key=WK("ab_type"))
            _ab_dur = st.number_input("Durée symptômes (min)", 0, 1440, 0, 1, key="ab_dur")
            _ab_res = calculer_abcd2(_ab_age, _ab_hta, _ab_type, float(_ab_dur), _ab_diab)
            _ab_v = _ab_res.get("score_val") or 0
            _ab_col = "#EF4444" if _ab_v >= 4 else "#F59E0B" if _ab_v >= 3 else "#22C55E"
            H(f'<div style="background:#0F172A;border-radius:8px;padding:12px;text-align:center;margin:8px 0;"><div style="font-size:.72rem;color:#64748B;">ABCD2</div><div style="font-size:2.2rem;font-weight:900;color:{_ab_col};">{_ab_v}/7</div></div>')
            AL(_ab_res.get("interpretation",""), "danger" if _ab_v >= 4 else "warning" if _ab_v >= 3 else "success")
            AL(_ab_res.get("recommendation",""), "info")
            CARD_END()

        with _n2c:
            CARD("PERC Rule — Exclusion EP sans D-Dimères", "")
            st.caption("Kline JA et al., J Thromb Haemost 2004")
            AL("Valide SEULEMENT si Wells EP ≤ 1 et probabilité < 15 %", "warning")
            _pr1, _pr2 = st.columns(2)
            _p_age = _pr1.checkbox("Âge > 50 ans",       key=WK("perc_age"), value=age > 50)
            _p_fc  = _pr2.checkbox("FC > 100/min",        key=WK("perc_fc"),  value=(SS.v_fc or 80) > 100)
            _p_sp  = _pr1.checkbox("SpO2 < 95 %",         key=WK("perc_sp"),  value=(SS.v_spo2 or 98) < 95)
            _p_he  = _pr2.checkbox("Hémoptysie",          key=WK("perc_he"))
            _p_op  = _pr1.checkbox("Oestroprogestatifs",  key=WK("perc_oe"))
            _p_ch  = _pr2.checkbox("Chir/trauma < 4 sem",key=WK("perc_ch"))
            _p_at  = _pr1.checkbox("ATCD TVP/EP",         key=WK("perc_at"))
            _p_oo  = _pr2.checkbox("Œdème unilatéral",   key=WK("perc_oo"))
            _pr_res = calculer_perc(_p_age, _p_fc, _p_sp, _p_he, _p_op, _p_ch, _p_at, _p_oo)
            _pv = _pr_res.get("score_val") or 0
            AL(_pr_res.get("interpretation",""), "success" if _pv == 0 else "danger")
            AL(_pr_res.get("recommendation",""), "info")
            CARD_END()

        CARD("GRACE Score — SCA pronostic (complément HEART/TIMI)", "")
        st.caption("Eagle KA et al., JAMA 2004")
        _gc1, _gc2, _gc3, _gc4 = st.columns(4)
        _gr_cr  = _gc1.number_input("Créatinine (µmol/l)", 0, 2000, 90, key="gr_cr")
        _gr_kp  = _gc2.select_slider("Killip", [1,2,3,4], key="gr_kp",
            format_func=lambda x:{1:"I–Pas IC",2:"II–Râles",3:"III–OAP",4:"IV–Choc"}[x])
        _gr_ac  = _gc3.checkbox("Arrêt cardiaque",   key=WK("gr_ac"))
        _gr_st  = _gc4.checkbox("Déviation ST",      key=WK("gr_st"))
        _gr_enz = _gc3.checkbox("Enzymes positives", key=WK("gr_enz"))
        _gr_res = calculer_grace(age, SS.v_fc or 80, SS.v_pas or 120,
            float(_gr_cr), _gr_ac, _gr_st, _gr_enz, int(_gr_kp))
        _gv = _gr_res.get("score_val") or 0
        _gc = "#EF4444" if _gv >= 140 else "#F59E0B" if _gv >= 109 else "#22C55E"
        H(f'<div style="background:#0F172A;border-radius:8px;padding:12px;display:flex;align-items:center;gap:16px;margin:8px 0;"><div style="text-align:center;min-width:80px;"><div style="font-size:.72rem;color:#64748B;">GRACE</div><div style="font-size:2.2rem;font-weight:900;color:{_gc};">{_gv}</div></div><div style="font-size:.78rem;color:#94A3B8;flex:1;">{_gr_res.get("interpretation","")}</div></div>')
        AL(_gr_res.get("recommendation",""), "danger" if _gv >= 140 else "warning" if _gv >= 109 else "info")
        CARD_END()

        if _nihss_priority:
            H('<div class="smart-tab-note muted">NIHSS déjà affiché en priorité en haut de l’onglet Scores.</div>')
        else:
            _render_nihss_rapide(WK)

        CARD("PRAM — Asthme pédiatrique (0-12)", "")
        st.caption("Chalut DS et al., J Pediatr 2000 | Sévérité GINA pédiatrique")
        AL("PRAM < 4 : léger | 4-7 : modéré | ≥ 8 : sévère → appel pédiatre immédiat", "info")
        _pm1, _pm2 = st.columns(2)
        _pr_spo2 = float(SS.v_spo2 or 98)
        _pr_tss  = _pm1.checkbox("Tirage sus-sternal", key=WK("pr_tss"))
        _pr_tsc  = _pm2.checkbox("Tirage sous-costal", key=WK("pr_tsc"))
        _pr_ti   = _pm1.checkbox("Tirage intercostal", key=WK("pr_ti"))
        _pr_ea   = _pm2.select_slider(
            "Entrée d'air",
            options=[1,2,3],
            format_func=lambda x:{1:"Normale",2:"Diminuée",3:"Très diminuée/absente"}[x],
            key=WK("pr_ea"))
        _pr_wh   = _pm1.select_slider(
            "Wheezing",
            options=[1,2,3,4],
            format_func=lambda x:{1:"Absent",2:"Expi seul",3:"Inspi+expi",4:"Audible sans stétho"}[x],
            key=WK("pr_wh"))
        _pr_res = calculer_pram(
            _pr_spo2, bool(_pr_tss), bool(_pr_tsc), bool(_pr_ti), int(_pr_ea), int(_pr_wh))
        _pv3 = _pr_res.get("score_val") or 0
        _pc3 = "#EF4444" if _pv3 >= 8 else "#F59E0B" if _pv3 >= 4 else "#22C55E"
        H(f'<div style="background:#0F172A;border-radius:8px;padding:12px;text-align:center;margin:8px 0;">'
          f'<div style="font-size:.72rem;color:#64748B;">PRAM</div>'
          f'<div style="font-size:2.2rem;font-weight:900;color:{_pc3};">{_pv3}/12</div></div>')
        AL(_pr_res.get("interpretation",""), "danger" if _pv3 >= 8 else "warning" if _pv3 >= 4 else "success")
        AL(_pr_res.get("recommendation",""), "info")
        CARD_END()

    # ── SC[4] PÉDIATRIE + SEVRAGE ─────────────────────────────────────────────
    with _SC[4]:
        with st.expander("ℹ️ Comprendre les scores Pédia / Sevrage", expanded=False):
            _e1, _e2 = st.columns(2)
            with _e1:
                explain("pews")
                explain("pram")
                explain("croup")
            with _e2:
                explain("ciwa")
                explain("algoplus")
                explain("cfs")
        _sp1, _sp2 = st.columns(2)
        with _sp1:
            CARD("PEWS — Dégradation pédiatrique précoce", "")
            st.caption("Monaghan A, Paediatric Nursing 2005")
            if age >= 18:
                AL("PEWS réservé aux patients < 18 ans", "info")
            else:
                _pw_co = st.select_slider("Comportement", [0,1,2,3,4], key=WK("pw_co"),
                    format_func=lambda x:{0:"Normal",1:"Dormant",2:"Irritable",3:"Réduit",4:"Inconscient"}[x])
                _pw_ca = st.select_slider("Cardiovasculaire", [0,1,2,3], key=WK("pw_ca"),
                    format_func=lambda x:{0:"Rosé CF≤2s",1:"Pâle CF>2s",2:"Gris CF≥3s",3:"Gris+tachy"}[x])
                _pw_re = st.select_slider("Respiratoire", [0,1,2,3], key=WK("pw_re"),
                    format_func=lambda x:{0:"Normal",1:"Tachypnée",2:"Tirage modéré",3:"Tirage sévère"}[x])
                _pews_res = calculer_pews(int(_pw_co), int(_pw_ca), int(_pw_re))
                _pv2 = _pews_res.get("score_val") or 0
                _pc2 = "#EF4444" if _pv2 >= 5 else "#F59E0B" if _pv2 >= 3 else "#22C55E"
                H(f'<div style="background:#0F172A;border-radius:8px;padding:12px;text-align:center;margin:8px 0;"><div style="font-size:.72rem;color:#64748B;">PEWS</div><div style="font-size:2.2rem;font-weight:900;color:{_pc2};">{_pv2}/9</div></div>')
                AL(_pews_res.get("interpretation",""), "danger" if _pv2 >= 5 else "warning" if _pv2 >= 3 else "success")
                AL(_pews_res.get("recommendation",""), "info")
            CARD_END()

            CARD("🧒 Outils pédiatriques rapides", "")
            if 0 < age < 13:
                _p_est = poids_estime_enfant(age)
                _sc_m  = surface_corporelle_mosteller(poids, taille) if taille > 0 else None
                _oa1, _oa2 = st.columns(2)
                _oa1.metric("Poids estimé APLS", f"{_p_est:.0f} kg" if _p_est else "N/A",
                    delta=f"{poids - _p_est:.0f} kg vs réel" if _p_est else None)
                _oa2.metric("SC Mosteller", f"{_sc_m:.2f} m²" if _sc_m else "N/A")
                if _p_est and abs(poids - _p_est) > 5:
                    AL(f"Écart poids réel/estimé > 5 kg — vérifier le poids saisi", "warning")
            else:
                AL("Formules APLS valables jusqu'à 12 ans — utiliser le poids réel", "info")
            st.divider()
            H('<div style="font-size:.72rem;font-weight:700;color:#64748B;margin-bottom:4px;">Croup — Score de Westley</div>')
            _cg1, _cg2 = st.columns(2)
            _cr_str = _cg1.select_slider("Stridor", [0,1,2], key=WK("cr_str"),
                format_func=lambda x:{0:"Absent",1:"Au repos",2:"Sévère"}[x])
            _cr_tir = _cg2.select_slider("Tirage", [0,1,2,3], key=WK("cr_tir"),
                format_func=lambda x:{0:"Absent",1:"Léger",2:"Modéré",3:"Sévère"}[x])
            _cr_air = _cg1.select_slider("Entrée air", [0,1,2], key=WK("cr_air"),
                format_func=lambda x:{0:"Normale",1:"Diminuée",2:"Très diminuée"}[x])
            _cr_con = _cg2.select_slider("Conscience", [0,1,2,3,4,5], key=WK("cr_con"),
                format_func=lambda x:{0:"Normale",1:"Agitée",2:"Irritable",3:"Léthargique",4:"Stuporeux",5:"Coma"}[x])
            _cr_cya = st.checkbox("Cyanose / SatO₂ basse", key=WK("cr_cya"))
            _croup_res = calculer_croup(int(_cr_str), int(_cr_tir), bool(_cr_cya),
                                        int(_cr_air), int(_cr_con))
            _cv3 = _croup_res.get("score_val") or 0
            _cc3 = "#EF4444" if _cv3 >= 6 else "#F59E0B" if _cv3 >= 3 else "#22C55E"
            H(f'<div style="background:#0F172A;border-radius:8px;padding:10px;text-align:center;margin:6px 0;">'
              f'<div style="font-size:.72rem;color:#64748B;">Westley</div>'
              f'<div style="font-size:2rem;font-weight:900;color:{_cc3};">{_cv3}/17</div></div>')
            AL(_croup_res.get("interpretation",""), "danger" if _cv3 >= 6 else "warning" if _cv3 >= 3 else "success")
            AL(_croup_res.get("recommendation",""), "info")
            CARD_END()

        with _sp2:
            CARD("CIWA-Ar — Sevrage alcoolique", "")
            st.caption("Sullivan JT et al., Br J Addict 1989")
            AL("Évaluer toutes les heures — Thiamine 500 mg IV AVANT tout glucosé", "warning")
            _ci_nv = st.slider("Nausées / vomissements (0-7)", 0, 7, 0, key=WK("ci_nv"))
            _ci_tr = st.slider("Tremblements (0-7)",           0, 7, 0, key=WK("ci_tr"))
            _ci_su = st.slider("Sudation (0-7)",               0, 7, 0, key=WK("ci_su"))
            _ci_ax = st.slider("Anxiété (0-7)",                0, 7, 0, key=WK("ci_ax"))
            _ci_ag = st.slider("Agitation (0-7)",              0, 7, 0, key=WK("ci_ag"))
            _ci_tt = st.slider("Troubles tactiles (0-7)",       0, 7, 0, key=WK("ci_tt"))
            _ci_ta = st.slider("Troubles auditifs (0-7)",       0, 7, 0, key=WK("ci_ta"))
            _ci_tv = st.slider("Troubles visuels (0-7)",        0, 7, 0, key=WK("ci_tv"))
            _ci_ce = st.slider("Céphalée (0-7)",                0, 7, 0, key=WK("ci_ce"))
            _ci_or = st.slider("Désorientation (0-4)",          0, 4, 0, key=WK("ci_or"))
            _ciwa_res = calculer_ciwa(_ci_nv,_ci_tr,_ci_su,_ci_ax,_ci_ag,_ci_tt,_ci_ta,_ci_tv,_ci_ce,_ci_or)
            _cv2 = _ciwa_res.get("score_val") or 0
            _cc2 = "#EF4444" if _cv2 >= 20 else "#F59E0B" if _cv2 >= 8 else "#22C55E"
            H(f'<div style="background:#0F172A;border-radius:8px;padding:12px;text-align:center;margin:8px 0;"><div style="font-size:.72rem;color:#64748B;">CIWA-Ar</div><div style="font-size:2.2rem;font-weight:900;color:{_cc2};">{_cv2}/67</div></div>')
            AL(_ciwa_res.get("interpretation",""), "danger" if _cv2 >= 20 else "warning" if _cv2 >= 8 else "success")
            AL(_ciwa_res.get("recommendation",""), "info")
            CARD_END()

            CARD("🤰 Terme de grossesse — Règle de Naegele", "")
            st.caption("Naegele FC 1812 — terme = DDR + 280 jours (40 SA)")
            _ddr_str = st.text_input("Date des dernières règles (JJ/MM/AAAA)",
                placeholder="ex: 15/03/2024", key=WK("ddr_input"))
            if _ddr_str:
                _terme_res = terme_naegele(_ddr_str)
                if _terme_res:
                    AL(_terme_res, "info")
                    try:
                        for _fmt in ('%d/%m/%Y','%Y-%m-%d','%d-%m-%Y'):
                            try:
                                _ddr_d = datetime.strptime(_ddr_str.strip(), _fmt); break
                            except ValueError: continue
                        _sa = (datetime.now() - _ddr_d).days // 7
                        if _sa >= 36:
                            AL(f"Grossesse ≥ 36 SA — Contacter maternité IMMÉDIATEMENT", "danger")
                        elif _sa >= 22:
                            AL(f"Grossesse {_sa} SA — Position latérale gauche si allongée", "warning")
                    except Exception:
                        pass
                else:
                    AL("Format invalide — utiliser JJ/MM/AAAA", "warning")
            CARD_END()

    # ── SC[5] TOXICOLOGIE ─────────────────────────────────────────────────────
    with _SC[5]:
        H('''<div style="background:linear-gradient(135deg,#1E293B,#334155);color:#fff;
            border-radius:10px;padding:12px 16px;margin-bottom:12px;display:flex;align-items:center;gap:12px;">
          <div style="font-size:1.8rem;">☠️</div>
          <div>
            <div style="font-size:.72rem;opacity:.75;text-transform:uppercase;letter-spacing:.1em;">Urgences toxicologiques</div>
            <div style="font-size:.95rem;font-weight:800;">Évaluation des intoxications médicamenteuses</div>
            <div style="font-size:.68rem;opacity:.7;margin-top:2px;">CBP Belgique : 070 / 245.245 (24h/24)</div>
          </div>
        </div>''')

        with st.expander("ℹ️ Comprendre les concepts toxicologiques", expanded=False):
            _e1, _e2 = st.columns(2)
            with _e1:
                explain("toxidrome")
                explain("pss")
            with _e2:
                explain("paracetamol_intox")
                explain("tricycliques_ecg")

        _TOX = st.tabs(["🎯 Toxidrome", "📊 PSS", "💊 Paracétamol", "❤️ Tricycliques / ECG", "🏥 TOXIC2"])

        with _TOX[0]:
            H('<div class="card-title">🎯 Reconnaissance du syndrome toxidromique</div>')
            st.caption("Isbister GK et al., J Toxicol 2004 — 7 syndromes cliniques reconnus")
            _signes_all = [
                "Myosis", "Mydriase", "Bradycardie", "Tachycardie",
                "Hypotension", "HTA", "Bradypnée", "Tachypnée",
                "Coma", "Agitation", "Convulsions", "Hallucinations",
                "Hyperthermie", "Hypothermie", "Peau sèche", "Diaphorèse",
                "Sialorrhée", "Bronchorrhée", "Hyperréflexie", "Hyporéflexie",
                "Clonus", "Iléus", "Rétention urinaire", "Fasciculations",
            ]
            st.markdown("**Cocher les signes présents :**")
            _sc1, _sc2, _sc3 = st.columns(3)
            _signes_coches = []
            for _i, _s in enumerate(_signes_all):
                _col = [_sc1, _sc2, _sc3][_i % 3]
                if _col.checkbox(_s, key=WK(f"tox_s_{_s}")):
                    _signes_coches.append(_s)

            if _signes_coches:
                _toxidromes_trouvés = identifier_toxidrome(_signes_coches)
                if _toxidromes_trouvés:
                    st.divider()
                    H('<div class="card-title">🔍 Toxidromes compatibles (par pertinence)</div>')
                    for _idx, _t in enumerate(_toxidromes_trouvés[:3]):
                        _t_css = "#FEF2F2" if _t["alerte"] == "danger" else "#FFFBEB"
                        _t_bdr = "#EF4444" if _t["alerte"] == "danger" else "#F59E0B"
                        _concordants_txt = ", ".join(_t.get("_concordants", []))
                        H(f'''<div style="background:{_t_css};border-left:4px solid {_t_bdr};
                            border-radius:0 10px 10px 0;padding:12px 16px;margin:6px 0;">
                          <div style="font-weight:800;font-size:.88rem;color:#1E293B;">
                            #{_idx+1} — {_t["nom"]}
                            <span style="font-size:.7rem;font-weight:400;color:#64748B;margin-left:8px;">
                              {_t.get("_score",0)} signe(s) concordant(s)
                            </span>
                          </div>
                          <div style="font-size:.73rem;color:#374151;margin-top:4px;">
                            Signes concordants : <em>{_concordants_txt}</em>
                          </div>
                          <div style="font-size:.73rem;margin-top:4px;color:#374151;">
                            <strong>Molécules :</strong> {_t["molecules"]}
                          </div>
                          <div style="background:{"#EF444420" if _t["alerte"]=="danger" else "#F59E0B20"};
                              border-radius:6px;padding:7px 10px;margin-top:6px;font-size:.78rem;font-weight:600;color:{_t_bdr};">
                            💊 Antidote : {_t["antidote"]}
                          </div>
                        </div>''')
                else:
                    AL("Aucun toxidrome identifié clairement — Appel CBP 070/245.245", "info")
            else:
                st.info("Cocher les signes cliniques pour identifier le toxidrome — ou consulter la référence ci-dessous")
                for _t in TOXIDROMES:
                    with st.expander(f"{'🔴' if _t['alerte']=='danger' else '🟠'} {_t['nom']}"):
                        st.markdown(f"**Signes :** {' | '.join(_t['signes'])}")
                        st.markdown(f"**Molécules :** {_t['molecules']}")
                        AL(f"Antidote : {_t['antidote']}", _t['alerte'])

        with _TOX[1]:
            H('<div class="card-title">📊 PSS — Poisoning Severity Score (0-4)</div>')
            st.caption("Persson HE et al., Eur J Clin Pharmacol 1998 — Standard EAPCCT")
            st.markdown("Coter chaque système sur 0-4 — Le score final = grade le plus élevé")
            _pss_scores = {}
            for _sys_name, _sys_grades in PSS_CRITERES.items():
                H(f'<div class="card-title" style="margin-top:10px;">{_sys_name}</div>')
                _pss_scores[_sys_name] = st.select_slider(
                    f"Grade {_sys_name}",
                    options=[0, 1, 2, 3, 4],
                    value=0,
                    key=WK(f"pss_{_sys_name}"),
                    format_func=lambda x, _grades=_sys_grades: f"{x} — {_grades[x]}",
                    label_visibility="collapsed",
                )
            _pss_res = calculer_pss(**{
                "neuro":       _pss_scores.get("Neurologique", 0),
                "cardio":      _pss_scores.get("Cardiovasculaire", 0),
                "respi":       _pss_scores.get("Respiratoire", 0),
                "digestif":    _pss_scores.get("Digestif", 0),
                "hepato_renal":_pss_scores.get("Hépatique/Rénal", 0),
            })
            _pss_v = _pss_res.get("score_val") or 0
            _pss_col = ["#22C55E","#3B82F6","#F59E0B","#EF4444","#7C3AED"][_pss_v]
            H(f'''<div style="background:{_pss_col}15;border:2px solid {_pss_col};
                border-radius:10px;padding:16px;text-align:center;margin:12px 0;">
              <div style="font-size:.72rem;color:#64748B;text-transform:uppercase;letter-spacing:.1em;">PSS</div>
              <div style="font-size:2.5rem;font-weight:900;color:{_pss_col};">{_pss_v}/4</div>
              <div style="font-size:.82rem;font-weight:700;color:{_pss_col};">{_pss_res.get("interpretation","")}</div>
            </div>''')
            AL(_pss_res.get("recommendation",""), "danger" if _pss_v >= 3 else "warning" if _pss_v >= 2 else "info")
            AL("CBP Belgique : 070 / 245.245 — Disponible 24h/24 7j/7", "info")

        with _TOX[2]:
            H('<div class="card-title">💊 Intoxication au paracétamol — Nomogramme Rumack-Matthew</div>')
            st.caption("Rumack BH et al., Arch Intern Med 1975 — MRCUK 2012 — BCFI Belgique")
            _pm_c1, _pm_c2 = st.columns(2)
            _pm_dose = _pm_c1.number_input("Dose ingérée estimée (mg/kg)", 0.0, 1000.0, 0.0, 10.0, key="pm_dose_intox")
            _pm_dose = _pm_dose if _pm_dose > 0 else None
            _pm_h = _pm_c2.number_input("Heure depuis ingestion (h)", 0.0, 72.0, 4.0, 0.5, key="pm_h")
            _pm_serique = _pm_c1.number_input("Paracétamolémie (µg/ml)", 0.0, 1000.0, 0.0, 5.0, key="pm_ser")
            _pm_serique = _pm_serique if _pm_serique > 0 else None
            st.markdown("**Facteurs de risque (seuil de traitement abaissé) :**")
            _rf1, _rf2 = st.columns(2)
            _pm_alcool  = _rf1.checkbox("Alcoolisme chronique",      key="pm_alc")
            _pm_hepato  = _rf2.checkbox("Hépatopathie chronique",    key="pm_hep")
            _pm_jeune   = _rf1.checkbox("Jeûne / dénutrition",       key="pm_jeu")
            _pm_induc   = _rf2.checkbox("Inducteurs enzymatiques (rifampicine, phénytoïne)", key="pm_ind")
            _pm_res = evaluer_paracetamol_intox(
                dose_mg_kg=_pm_dose, heure_ingestion=_pm_h,
                paracetamol_serique_mgL=_pm_serique,
                atcd_alcool=_pm_alcool, atcd_hepatique=_pm_hepato,
                atcd_jeune=_pm_jeune, medicaments_inducteurs=_pm_induc,
            )
            _pm_nac = _pm_res.get("nac_indiquee", False)
            _pm_col = "#EF4444" if _pm_nac else "#22C55E"
            H(f'''<div style="background:{_pm_col}15;border:3px solid {_pm_col};
                border-radius:10px;padding:14px;text-align:center;margin:10px 0;">
              <div style="font-size:1.1rem;font-weight:900;color:{_pm_col};">
                {"🔴 NAC INDIQUÉE" if _pm_nac else "🟢 NAC probablement non indiquée"}
              </div>
              <div style="font-size:.78rem;margin-top:6px;color:#374151;">{_pm_res.get("interpretation","")}</div>
            </div>''')
            if _pm_res.get("terrain_risque"):
                AL("Terrain à risque — Seuil de traitement abaissé (ligne 100 µg/ml au lieu de 150)", "warning")
            for _det in (_pm_res.get("details") or []):
                H(f'<div style="font-size:.75rem;color:#374151;padding:3px 0;">▶ {_det}</div>')
            st.divider()
            _nac_lines = [
                "① 150 mg/kg dans 200 ml G5 % en 1 h",
                "② 50 mg/kg dans 500 ml G5 % en 4 h",
                "③ 100 mg/kg dans 1000 ml G5 % en 16 h",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"Exemple {poids:.0f} kg : ① {int(150*poids)} mg | ② {int(50*poids)} mg | ③ {int(100*poids)} mg",
            ]
            _nac_lines_html = "".join(f"<div>{_ligne}</div>" for _ligne in _nac_lines)
            H(
                '<div style="background:#0F172A;border-radius:8px;padding:12px 16px;'
                'font-family:monospace;font-size:.75rem;color:#94A3B8;">'
                '<div style="color:#38BDF8;font-weight:700;margin-bottom:6px;">'
                'N-ACÉTYLCYSTÉINE IV (Fluimucil® Antidot) — Protocole 3 poches</div>'
                f'{_nac_lines_html}</div>'
            )
            AL("Appel CBP Belgique 070/245.245 pour conseil thérapeutique personnalisé", "info")

        with _TOX[3]:
            H('<div class="card-title">❤️ Antidépresseurs tricycliques / Toxiques cardiaques — Critères ECG</div>')
            st.caption("Boehnert MT, Lovejoy FH, NEJM 1985 / Kerr GW, Emerg Med J 2001")
            _tc1, _tc2 = st.columns(2)
            _tc_qrs = _tc1.number_input("QRS (ms)", 50, 300, 90, 5, key="tc_qrs")
            _tc_qtc = _tc2.number_input("QTc (ms)", 300, 700, 440, 10, key="tc_qtc")
            _tc_ravr = _tc1.number_input("Amplitude R en aVR (mm)", 0.0, 10.0, 0.0, 0.5, key="tc_ravr")
            _tc_rs = _tc2.number_input("Rapport R/S en aVR", 0.0, 5.0, 0.0, 0.1, key="tc_rs")
            _tc_bbd = st.checkbox("BBD ou morphologie S1Q3T3 (effet stabilisant membranaire)", key="tc_bbd")
            _tc_res = evaluer_tricycliques_ecg(
                qrs_ms=_tc_qrs, qtc_ms=_tc_qtc,
                r_avr_mv=_tc_ravr, rap_s_avr=_tc_rs,
                branche_droite=_tc_bbd,
            )
            _tc_v = _tc_res.get("score_val") or 0
            _tc_col = "#EF4444" if _tc_v >= 5 else "#F59E0B" if _tc_v >= 2 else "#22C55E"
            H(f'''<div style="background:{_tc_col}15;border:2px solid {_tc_col};
                border-radius:10px;padding:14px;margin:10px 0;">
              <div style="display:flex;align-items:center;gap:12px;">
                <div style="font-size:2rem;font-weight:900;color:{_tc_col};font-family:monospace;">{_tc_v}</div>
                <div>
                  <div style="font-size:.82rem;font-weight:700;color:{_tc_col};">{_tc_res.get("interpretation","")}</div>
                </div>
              </div>
            </div>''')
            for _ce in (_tc_res.get("criteres_ecg") or []):
                AL(_ce, "danger" if "Risque FV" in _ce or "≥ 160" in _ce else "warning")
            if _tc_res.get("bicarbonate_urgent"):
                H('''<div style="background:#7F1D1D;color:#FEE2E2;border-radius:8px;padding:14px;margin:10px 0;font-weight:700;">
                  🔴 BICARBONATE SODIQUE 8,4 % — INDIQUÉ<br>
                  <span style="font-size:.8rem;font-weight:400;">
                  Dose : 1-2 mEq/kg IV bolus (= 1-2 ml/kg de NaHCO3 8,4 %) | Cible pH 7,50-7,55<br>
                  Répéter toutes les 5-10 min jusqu'à rétrécissement QRS<br>
                  ⚠️ Eviter Flécaïnide, Lidocaïne, physostigmine
                  </span>
                </div>''')
            st.divider()
            AL(_tc_res.get("recommendation",""), "danger" if _tc_v >= 5 else "warning" if _tc_v >= 2 else "info")
            H('<div class="card-title" style="margin-top:12px;">Antidotes spécifiques par classe</div>')
            for _ant in [
                ("Tricycliques (ADT)",  "Bicarbonate NaHCO3 8,4 % — 1-2 mEq/kg IV si QRS ≥ 100 ms"),
                ("Digitaliques",        "Anticorps anti-digitaliques (Digifab®) — 38 mg par ng/ml de digoxinémie × poids"),
                ("Bêtabloquants",       "Glucagon 3-5 mg IV bolus + HDES (High-dose Epinephrine) + Intralipid® 20 %"),
                ("Anticalciques",       "Chlorure de calcium IV + Glucagon + Insuline haute dose + Intralipid® 20 %"),
                ("Antiarythmiques (Ic)","Bicarbonate + Intralipid® 20 % si FV réfractaire — ECMO si disponible"),
            ]:
                H(f'<div style="background:#F8FAFC;border-left:3px solid #7C3AED;border-radius:0 8px 8px 0;'
                   f'padding:8px 14px;margin:4px 0;font-size:.78rem;">'
                   f'<strong style="color:#5B21B6;">{_ant[0]}</strong><br>{_ant[1]}</div>')

        with _TOX[4]:
            H('<div class="card-title">🏥 TOXIC2 — Niveau de soins requis</div>')
            st.caption("Eyer F et al., Clin Toxicol 2009 — Score ≥ 2 → hospitalisation USI")
            _tx1, _tx2 = st.columns(2)
            _tx_gcs  = _tx1.number_input("GCS actuel", 3, 15, int(SS.v_gcs or 15), key="tx_gcs")
            _tx_fc   = _tx1.checkbox(f"FC < 50 ou > 130 bpm (actuelle : {SS.v_fc or 80:.0f})",
                key="tx_fc", value=bool(SS.v_fc and (SS.v_fc < 50 or SS.v_fc > 130)))
            _tx_pas  = _tx2.checkbox(f"PAS < 90 mmHg (actuelle : {SS.v_pas or 120:.0f})",
                key="tx_pas", value=bool(SS.v_pas and SS.v_pas < 90))
            _tx_spo  = _tx2.checkbox(f"SpO2 < 92 % (actuelle : {SS.v_spo2 or 98:.0f}%)",
                key="tx_spo", value=bool(SS.v_spo2 and SS.v_spo2 < 92))
            _tx_qrs  = _tx1.checkbox("QRS ≥ 120 ms à l'ECG", key="tx_qrs")
            _tx_qtc  = _tx2.checkbox("QTc > 500 ms", key="tx_qtc")
            _tx_card = _tx1.checkbox("Molécule cardiotoxique (ADT, digitaliques, BB, anticalciques)",
                key="tx_card")
            _tx_mul  = _tx2.checkbox("Poly-intoxication (≥ 2 molécules)", key="tx_mul")
            _tx_ts   = st.checkbox("Contexte de tentative de suicide (évaluation psychiatrique requise)",
                key="tx_ts")
            _tx_res = calculer_toxic2(
                gcs=_tx_gcs, fc_anormale=_tx_fc, pas_basse=_tx_pas,
                spo2_basse=_tx_spo, qrs_large=_tx_qrs, qtc_long=_tx_qtc,
                molecule_cardiotoxique=_tx_card, intox_multiple=_tx_mul,
                tentative_suicide=_tx_ts,
            )
            _tx_v   = _tx_res.get("score_val") or 0
            _tx_col = "#EF4444" if _tx_v >= 5 else "#F59E0B" if _tx_v >= 3 else "#3B82F6" if _tx_v >= 1 else "#22C55E"
            _tx_lbl = ["🟢 Ambulatoire / Obs. 4-6h","🔵 Hospitalisation","🟠 USI recommandée","🔴 Réanimation"][min(3, max(0,_tx_v//2 if _tx_v < 5 else 3))]
            H(f'''<div style="background:{_tx_col}15;border:3px solid {_tx_col};
                border-radius:12px;padding:18px;text-align:center;margin:12px 0;">
              <div style="font-size:2rem;font-weight:900;color:{_tx_col};font-family:monospace;">{_tx_v}</div>
              <div style="font-size:.9rem;font-weight:700;color:{_tx_col};">{_tx_lbl}</div>
              <div style="font-size:.75rem;color:#374151;margin-top:4px;">{_tx_res.get("interpretation","")}</div>
            </div>''')
            for _item in (_tx_res.get("items_positifs") or []):
                AL(_item, "danger" if any(k in _item for k in ["Coma","< 90","< 92","FV"]) else "warning")
            AL(_tx_res.get("recommendation",""), "danger" if _tx_v >= 5 else "warning" if _tx_v >= 3 else "info")
            if _tx_ts:
                st.divider()
                H('''<div style="background:#1E3A5F;color:#93C5FD;border-radius:8px;padding:12px 16px;font-size:.78rem;">
                  <div style="font-weight:700;margin-bottom:6px;">📋 Évaluation psychiatrique obligatoire</div>
                  <div>• Évaluation du risque suicidaire avant sortie</div>
                  <div>• Contrat de soins si retour à domicile</div>
                  <div>• Sécurisation de l'environnement (médicaments, objets dangereux)</div>
                  <div>• Ligne de crise : 0800 / 32.123 (Prévention Suicide Belgique)</div>
                </div>''')
            st.divider()
            H('''<div style="background:#0F172A;border-radius:8px;padding:12px 16px;font-size:.72rem;color:#94A3B8;">
              <div style="color:#38BDF8;font-weight:700;margin-bottom:6px;">☎️ CONTACTS TOXICOLOGIE</div>
              <div>🇧🇪 <strong style="color:#fff;">Centre Belge Anti-Poisons (CBP)</strong> — 070 / 245.245</div>
              <div>🌍 EAPCCT — European Ass. of Poisons Centres</div>
              <div style="margin-top:6px;">⚠️ Toujours appeler le CBP pour toute intoxication grave</div>
            </div>''')
