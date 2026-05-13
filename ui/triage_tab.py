# ui/triage_tab.py — Onglet Triage — AKIR-IAO v20
# Logique extraite de streamlit_app.py T[1] (modularisation)
from __future__ import annotations
import streamlit as st
from datetime import datetime

from config import NEWS2_TRI_M, DELAIS, LABELS, SECTEURS, TCSS, ATCD
from clinical.news2 import (
    calculer_news2,
    pews_meta, seuils_normaux_ped,
    calculer_pews as calculer_pews_vitaux,
)
from clinical.triage import french_triage, process_voice_triage, verifier_coherence
from clinical.vitaux import si, sipa
from clinical.french_v12 import (
    FRENCH_MOTS_CAT,
    get_protocol, render_discriminants, apply_discriminant_selection,
    DISCRIMINANTS_ENRICHIS, render_discriminants_enrichis, process_answers,
)
from persistence.registry import enregistrer_patient
from akir_iao_enhancements import (
    gcs_visual_scale, borg_visual_scale, cam_icu_visual,
    sync_clinical_context, render_smart_alerts, render_next_steps,
)
from ui.components import H, AL, EVA_BAR, SBAR_RENDER, build_sbar

MOTS_CAT = FRENCH_MOTS_CAT

_VOICE_ATCD_WIDGETS = {
    "HTA": "pt_hta",
    "Insuffisance cardiaque": "pt_ic",
    "Coronaropathie / SCA antérieur": "pt_coro",
    "AVC / AIT antérieur": "pt_avc",
    "BPCO": "pt_bpco",
    "Asthme": "pt_asthme",
    "Diabète type 2": "pt_diab2",
    "Diabète type 1": "pt_diab1",
    "Insuffisance rénale chronique": "pt_ir",
    "Insuffisance hépatique": "pt_ih",
    "Épilepsie": "pt_epi",
    "Fibrillation atriale": "pt_fa",
    "Drépanocytose": "pt_drep",
    "Immunodépression": "pt_immuno",
}

_VOICE_RISK_WIDGETS = {
    "Grossesse": "pt_gros",
    "Obésité morbide (IMC ≥ 40)": "pt_ob",
}

_VOICE_TRT_WIDGETS = {
    "Anticoagulants/AOD": "pt_acg",
    "Antiagrégants plaquettaires": "pt_aap",
    "Bêta-bloquants": "pt_beta",
    "Corticoïdes au long cours": "pt_cort",
    "IMAO (inhibiteurs MAO)": "pt_imao",
    "Chimiothérapie en cours": "pt_chimo",
}


@st.cache_data(show_spinner=False, max_entries=200)
def _calc_news2_triage(fr, spo2, o2, temp, pas, fc, gcs, bpco):
    """Pure wrapper cacheable. Lève ValueError sur vitaux invalides."""
    n2, _ = calculer_news2(fr, spo2, o2, temp, pas, fc, gcs, bpco)
    return n2


def _calc_news2_safe(fr, spo2, o2, temp, pas, fc, gcs, bpco):
    """Variante UI : retourne None et affiche l'erreur si vitaux invalides."""
    try:
        return _calc_news2_triage(fr, spo2, o2, temp, pas, fc, gcs, bpco)
    except ValueError as exc:
        st.error(f"🚨 NEWS2 indisponible — {exc}")
        return None


def _wk(base: str, scope: str | None = None) -> str:
    SS = st.session_state
    parts = [str(SS.get("uid") or SS.get("sid") or "s")]
    if scope:
        parts.append(str(scope))
    parts.append(str(base))
    return "__".join(p.replace(" ", "_") for p in parts if p)


def apply_voice_triage_to_session(SS=None, WK=None) -> bool:
    """Applique une extraction vocale en attente avant la création des widgets."""
    SS = SS if SS is not None else st.session_state
    WK = WK or _wk
    data = SS.pop("voice_triage_pending", None)
    if not isinstance(data, dict):
        return False

    age = data.get("age")
    age_mois = data.get("age_mois")
    if age is not None:
        try:
            SS["age"] = float(age)
            SS["age_mois"] = 0
            SS["pt_age"] = int(float(age))
            SS["smart_ped_vitals"] = float(age) < 15
        except (TypeError, ValueError):
            pass
    elif age_mois is not None:
        try:
            mois = int(float(age_mois))
            SS["age"] = round(mois / 12.0, 4)
            SS["age_mois"] = mois
            SS["pt_age"] = 0
            SS["pt_am"] = mois
            SS["smart_ped_vitals"] = True
        except (TypeError, ValueError):
            pass

    if data.get("sexe") in ("Masculin", "Féminin", "Non précisé"):
        SS["pt_sex"] = data["sexe"]

    category = data.get("categorie") or ""
    motif = data.get("motif") or ""
    if category in MOTS_CAT and motif in MOTS_CAT[category]:
        SS["cat"] = category
        SS["motif"] = motif
        SS["tr_cat"] = category
        SS["tr_mot"] = motif

    atcd_found = [a for a in data.get("atcd", []) if a in ATCD]
    if atcd_found:
        current = [a for a in SS.get("atcd", []) if a in ATCD]
        merged = [a for a in ATCD if a in set(current + atcd_found)]
        SS["atcd"] = merged
        other = []
        for label in merged:
            if label in _VOICE_ATCD_WIDGETS:
                SS[WK(_VOICE_ATCD_WIDGETS[label])] = True
            elif label in _VOICE_RISK_WIDGETS:
                SS[WK(_VOICE_RISK_WIDGETS[label])] = True
            elif label in _VOICE_TRT_WIDGETS:
                SS[WK(_VOICE_TRT_WIDGETS[label])] = True
            else:
                other.append(label)
        SS["pt_atcd_other"] = [a for a in other if a in ATCD]

    pqrst = data.get("pqrst") if isinstance(data.get("pqrst"), dict) else {}
    if pqrst:
        det = dict(SS.get("det") or {})
        det["pqrst"] = pqrst
        det["voice_pqrst"] = pqrst
        SS["det"] = det
        sev = pqrst.get("severite")
        if sev is not None:
            try:
                sev_i = max(0, min(10, int(float(sev))))
                SS["eva"] = sev_i
                SS[WK("tr_eva")] = str(sev_i)
                pain_text = " ".join([
                    str(data.get("texte_anonymise") or ""),
                    str(data.get("motif") or ""),
                    " ".join(str(v) for v in pqrst.values() if v),
                ]).casefold()
                if sev_i >= 7 and ("douleur" in pain_text or pqrst.get("region") or pqrst.get("qualite")):
                    SS["pharmacie_auto_antalgie"] = True
                    SS["pharmacie_auto_antalgie_reason"] = f"Dictée clinique: douleur EVA {sev_i}/10"
            except (TypeError, ValueError):
                pass

    if data.get("allergies"):
        SS["alg"] = data["allergies"]
        SS["pt_alg"] = data["allergies"]

    constantes = data.get("constantes") if isinstance(data.get("constantes"), dict) else {}
    _vital_map = {
        "fc": ("v_fc", "tr_fc", int),
        "pas": ("v_pas", "tr_pas", int),
        "spo2": ("v_spo2", "tr_sp", int),
        "fr": ("v_fr", "tr_fr", int),
        "temperature": ("v_temp", "tr_t", float),
        "gcs": ("v_gcs", "tr_gcs", int),
    }
    for key, (ss_key, widget_key, caster) in _vital_map.items():
        value = constantes.get(key)
        if value is None:
            continue
        try:
            casted = caster(value)
        except (TypeError, ValueError):
            continue
        SS[ss_key] = casted
        SS[widget_key] = casted

    sync_clinical_context(SS)
    return True


def apply_new_triage_reset_to_session(SS=None, WK=None) -> bool:
    """Nettoie le contexte patient avant les widgets lors d'une nouvelle arrivée."""
    SS = SS if SS is not None else st.session_state
    WK = WK or _wk
    started_at = SS.pop("new_triage_reset_pending", None)
    if not started_at:
        return False

    first_cat = list(MOTS_CAT.keys())[0]
    first_motif = MOTS_CAT[first_cat][0]
    SS.update({
        "t_arr": datetime.fromisoformat(started_at) if isinstance(started_at, str) else datetime.now(),
        "t_cont": None,
        "t_reev": None,
        "v_temp": 37.0,
        "v_fc": 80,
        "v_pas": 120,
        "v_spo2": 98,
        "v_fr": 16,
        "v_gcs": 15,
        "v_news2": 0,
        "v_bpco": False,
        "age": 45,
        "age_mois": 0,
        "poids": 70,
        "taille": 170,
        "alg": "",
        "o2": False,
        "motif": first_motif,
        "cat": first_cat,
        "eva": 0,
        "gl": None,
        "niv": None,
        "just": "",
        "crit": "",
        "det": {},
        "uid_cur": None,
        "histo": [],
        "reevs": [],
        "atcd": [],
        "atcd_checks": {},
        "risk_checks": {},
        "trt_checks": {},
        "voice_triage_last": None,
        "voice_triage_pending": None,
        "pharmacie_auto_antalgie": False,
        "pharmacie_auto_antalgie_reason": "",
        "smart_ped_vitals": False,
        "smart_context": {},
    })

    widget_defaults = {
        "pt_age": 45,
        "pt_am": 0,
        "pt_sex": "Non précisé",
        "pt_kg": 70,
        "pt_taille": 170,
        "pt_alg": "",
        "pt_atcd_other": [],
        "tr_fc": 80,
        "tr_pas": 120,
        "tr_sp": 98,
        "tr_fr": 16,
        "tr_t": 37.0,
        "tr_gcs": 15,
        "tr_gl": 0,
        "tr_cat": first_cat,
        "tr_mot": first_motif,
    }
    for key, value in widget_defaults.items():
        SS[key] = value
    SS[WK("tr_eva")] = "0"
    SS[WK("tr_bp")] = False
    SS[WK("voice_text")] = ""
    for suffix in {
        *_VOICE_ATCD_WIDGETS.values(),
        *_VOICE_RISK_WIDGETS.values(),
        *_VOICE_TRT_WIDGETS.values(),
        "pt_allait", "pt_chir", "pt_tabac", "pt_o2",
    }:
        SS[WK(suffix)] = False
    return True


def render() -> None:
    SS = st.session_state
    WK = _wk

    age   = float(SS.get("age") or 45)
    poids = float(SS.get("poids") or 70)
    atcd  = list(SS.get("atcd") or [])
    alg   = str(SS.get("alg") or "")
    o2    = bool(SS.get("o2") or False)
    _si_val = 0.0  # valeur par défaut si PAS <= 0
    _smart = sync_clinical_context(SS)

    H("""<style>
    @media (max-width: 768px) {
      button[kind="primary"] {
        background:#16A34A !important;
        border-color:#15803D !important;
        color:#fff !important;
        width:100% !important;
        transition:transform .08s ease, filter .12s ease, background-color .12s ease;
      }
      button[kind="primary"]:active {
        transform:scale(.985);
        filter:brightness(1.12);
        background:#22C55E !important;
      }
    }
    </style>""")

    _last_voice = SS.get("voice_triage_last")
    if isinstance(_last_voice, dict):
        _src = _last_voice.get("source", "NLP")
        _parts = [
            f"{_last_voice.get('age')} ans" if _last_voice.get("age") is not None else "",
            _last_voice.get("sexe") or "",
            _last_voice.get("motif") or "",
        ]
        _summary = " · ".join(p for p in _parts if p)
        AL(f"🎙️ Dictée clinique appliquée ({_src}) : {_summary or 'données partielles'}", "success")
        for _vw in _last_voice.get("warnings") or []:
            AL(_vw, "info")
        with st.expander("Voir les données extraites de la dictée", expanded=False):
            st.json({k: v for k, v in _last_voice.items() if k not in ("texte_anonymise", "_semantic")})
            _sem = _last_voice.get("_semantic")
            if _sem:
                st.markdown("**Analyse sémantique Claude (v2.0)**")
                _flags = _sem.get("flags_systeme") or {}
                _cols = st.columns(3)
                if _flags.get("news2_target_o2"):
                    _cols[0].metric("Cible SpO2", _flags["news2_target_o2"])
                if _flags.get("alerte_hemorragique"):
                    _cols[1].warning("⚠️ Risque hémorragique")
                if _flags.get("alerte_sepsis"):
                    _cols[2].warning("⚠️ Sepsis à évaluer")
                _atcd = _sem.get("atcd_matching") or []
                _traitement = _sem.get("traitements_detectes") or []
                if _atcd:
                    st.caption("ATCD détectés : " + " · ".join(_atcd))
                if _traitement:
                    st.caption("Traitements : " + " · ".join(_traitement))
                _ambigus = _sem.get("termes_ambigus") or []
                if _ambigus:
                    st.caption("Termes à clarifier : " + ", ".join(_ambigus))

    with st.expander("🎙️ Dictée Clinique — pré-remplissage sécurisé", expanded=False):
        st.caption(
            "Dicter ou coller une présentation patient. Les noms/prénoms détectés sont supprimés "
            "avant l'extraction; les champs incertains restent vides."
        )
        _voice_text = st.text_area(
            "Présentation dictée",
            placeholder=(
                "ex : Homme 67 ans, oppression thoracique depuis 45 min, EVA 8/10, "
                "ATCD stent, diabète, sous Eliquis..."
            ),
            height=110,
            key=WK("voice_text"),
            label_visibility="collapsed",
        )
        _v1, _v2 = st.columns([2, 1])
        if _v1.button("🎙️ Analyser et pré-remplir", type="primary", use_container_width=True, key=WK("voice_apply")):
            if not _voice_text.strip():
                AL("Dicter ou coller une présentation clinique avant l'analyse.", "warning")
            else:
                _voice_data = process_voice_triage(_voice_text)
                SS["voice_triage_pending"] = _voice_data
                SS["voice_triage_last"] = _voice_data
                st.rerun()
        if _v2.button("Effacer dictée", use_container_width=True, key=WK("voice_clear")):
            SS.pop("voice_triage_last", None)
            SS.pop("voice_triage_pending", None)
            SS[WK("voice_text")] = ""
            st.rerun()

    def _n2_compute() -> int | None:
        sync_clinical_context(SS)
        n2 = _calc_news2_safe(
            SS.v_fr, SS.v_spo2, SS.o2,
            SS.v_temp, SS.v_pas, SS.v_fc, SS.v_gcs, SS.v_bpco)
        SS.v_news2 = n2
        return n2

    # ── BLOC A : Chronomètre tactile ─────────────────────────────────────────
    _ta1, _ta2 = st.columns(2)
    if _ta1.button("⏱ Marquer arrivée", key="tr_arr", use_container_width=True):
        SS["new_triage_reset_pending"] = datetime.now().isoformat()
        st.rerun()
    if _ta2.button("👨‍⚕️ 1er contact médecin", key="tr_cont", use_container_width=True):
        SS.t_cont = datetime.now(); st.rerun()

    if SS.t_arr:
        _el = (datetime.now() - SS.t_arr).total_seconds()
        _m, _s = divmod(int(_el), 60)
        _col = "#EF4444" if _el > 600 else ("#F59E0B" if _el > 300 else "#22C55E")
        _crit_txt = "<div style='font-size:.75rem;color:#fff;font-weight:700;'>⚠️ DÉLAI CRITIQUE</div>" if _el > 600 else ""
        H(f'<div class="timer-widget" style="background:{_col}20;border:2px solid {_col};">'
          f'<div><div class="timer-label">Temps depuis arrivée</div>'
          f'<div class="timer-digits" style="color:{_col};">{_m:02d}:{_s:02d}</div></div>'
          f'{_crit_txt}'
          f'</div>')

    st.divider()

    # ── BLOC B : Constantes vitales — saisie dense ───────────────────────────
    H('<div class="card-title">📊 Constantes vitales</div>')

    _vc1, _vc2, _vc3 = st.columns(3)
    SS.v_fc   = _vc1.number_input("FC (bpm)",   20, 220, int(SS.v_fc),         key="tr_fc")
    SS.v_pas  = _vc2.number_input("PAS (mmHg)", 40, 260, int(SS.v_pas),        key="tr_pas")
    SS.v_spo2 = _vc3.number_input("SpO2 (%)",   50, 100, int(SS.v_spo2),       key="tr_sp")
    _vc4, _vc5, _vc6 = st.columns(3)
    SS.v_fr   = _vc4.number_input("FR (/min)",   5,  60, int(SS.v_fr),         key="tr_fr")
    SS.v_temp = _vc5.number_input("T° (°C)",    30.0, 45.0, float(SS.v_temp), 0.1, key="tr_t")
    SS.v_gcs  = _vc6.number_input("GCS (3-15)",  3,  15, int(SS.v_gcs),        key="tr_gcs")

    with st.expander("🧠 GCS détaillé par sous-scores", expanded=False):
        gcs_visual_scale()

    _bpco_key = WK("tr_bp")
    _bpco_locked = bool(_smart.get("bpco_forced"))
    if _bpco_locked:
        SS.v_bpco = True
        SS[_bpco_key] = True
        st.checkbox(
            "BPCO — utiliser SpO2 cible 88-92 %",
            key=_bpco_key,
            value=True,
            disabled=True,
            help="Forcé automatiquement par les antécédents.",
        )
        AL("BPCO détectée dans les antécédents — NEWS2 calcule avec la cible SpO2 88-92 %", "info")
    else:
        SS.v_bpco = st.checkbox(
            "BPCO — utiliser SpO2 cible 88-92 %",
            key=_bpco_key,
            value=bool(SS.v_bpco),
        )
    if SS.v_bpco:
        AL("BPCO actif — SpO2 > 96 % sous O₂ = RISQUE hypercapnie", "warning")
    if SS.get("smart_ped_vitals"):
        AL("Mode pédiatrique activé par la dictée — constantes interprétées avec PEWS.", "info")

    _n2 = _n2_compute()

    # ── PEWS — score pédiatrique si âge < 16 ans ─────────────────────────────
    if age < 16 and age > 0:
        _pews_s, _pews_al, _pews_md = calculer_pews_vitaux(
            fc=SS.v_fc, fr=SS.v_fr, spo2=SS.v_spo2, gcs=SS.v_gcs,
            temp=SS.v_temp, age_ans=age, supp_o2=o2)
        _pews_m   = pews_meta(_pews_s)
        _pews_col = _pews_m["color"]
        _pews_n   = seuils_normaux_ped(age)
        H(f'''<div style="background:{_pews_col}18;border:2px solid {_pews_col};
            border-radius:10px;padding:12px 16px;margin:8px 0;">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
              <div style="font-size:.72rem;color:#64748B;text-transform:uppercase;letter-spacing:.08em;">
                PEWS — Pédiatrie {_pews_n["label"]}
              </div>
              <div style="font-size:1.5rem;font-weight:900;color:{_pews_col};">{_pews_s}/9</div>
              <div style="font-size:.75rem;color:{_pews_col};font-weight:700;">{_pews_m["reco"]}</div>
            </div>
            <div style="text-align:right;font-size:.68rem;color:#64748B;line-height:1.6;">
              <div>FC : {_pews_n["fc"][0]}-{_pews_n["fc"][1]} bpm</div>
              <div>FR : {_pews_n["fr"][0]}-{_pews_n["fr"][1]} /min</div>
              <div>SpO2 ≥ {_pews_n["spo2_min"]} %</div>
            </div>
          </div>
        </div>''')
        for _pa in _pews_al:
            AL(_pa, "danger" if _pews_s >= 5 else "warning")
        if _pews_md.get("fc_anormale"):
            AL(f"FC {SS.v_fc:.0f} bpm hors norme pour {_pews_n['label']} (attendu {_pews_n['fc'][0]}-{_pews_n['fc'][1]})", "warning")
        if _pews_md.get("spo2_anormale"):
            AL(f"SpO2 {SS.v_spo2:.0f}% < cible {_pews_n['spo2_min']}% pour cet âge", "warning")
        H('<div style="font-size:.72rem;color:#94A3B8;margin:-4px 0 6px;">NEWS2 non validé avant 16 ans — PEWS utilisé (Monaghan 2005)</div>')

    # Affichage NEWS2 inline
    _n2_color = "#7C3AED" if _n2 >= 9 else "#EF4444" if _n2 >= 7 else "#F59E0B" if _n2 >= 5 else "#22C55E" if _n2 >= 1 else "#3B82F6"
    _n2_risk  = ("CRITIQUE — Déchocage" if _n2 >= 9 else
                 "ÉLEVÉ — Appel médecin immédiat" if _n2 >= 7 else
                 "MODÉRÉ — Surveillance rapprochée" if _n2 >= 5 else
                 "Faible — Surveillance standard" if _n2 >= 1 else "Stable")
    _bpco_sub = ('<div style="font-size:.72rem;color:#64748B;">Echelle SpO2-2 (BPCO)</div>' if SS.v_bpco else '')
    H(f'<div class="news2-inline">'
      f'<div class="news2-number" style="color:{_n2_color};">{_n2}</div>'
      f'<div><div class="news2-label">NEWS2 / 20</div>'
      f'{_bpco_sub}'
      f'</div></div>')

    if _n2 >= 9:
        H('<div style="background:#4C1D95;color:#E879F9;border-radius:8px;padding:10px;text-align:center;font-weight:800;font-size:.9rem;animation:pulse 1.5s infinite;margin:6px 0;">🟣 NEWS2 ≥ 9 — APPEL DÉCHOCAGE IMMÉDIAT</div>')
    elif _n2 >= 7:
        H('<div style="background:#7F1D1D;color:#FEE2E2;border-radius:8px;padding:10px;text-align:center;font-weight:800;font-size:.9rem;margin:6px 0;">🔴 NEWS2 ≥ 7 — APPEL MÉDICAL IMMÉDIAT</div>')

    def _vcss(v, lo, hi):
        return "crit" if (v < lo or v > hi) else ("warn" if (v < lo*1.08 or v > hi*0.93) else "")

    H(f'<div class="vg6">'
      f'<div class="vbox {_vcss(SS.v_fc,60,100)}"><div class="vbox-lbl">FC</div><div class="vbox-val">{SS.v_fc}</div></div>'
      f'<div class="vbox {_vcss(SS.v_pas,90,140)}"><div class="vbox-lbl">PAS</div><div class="vbox-val">{SS.v_pas}</div></div>'
      f'<div class="vbox {_vcss(SS.v_spo2,94,100)}"><div class="vbox-lbl">SpO₂%</div><div class="vbox-val">{SS.v_spo2}</div></div>'
      f'<div class="vbox {_vcss(SS.v_fr,12,20)}"><div class="vbox-lbl">FR</div><div class="vbox-val">{SS.v_fr}</div></div>'
      f'<div class="vbox {_vcss(SS.v_temp,36.0,38.0)}"><div class="vbox-lbl">T°C</div><div class="vbox-val">{SS.v_temp:.1f}</div></div>'
      f'<div class="vbox {_vcss(SS.v_gcs,14,15)}"><div class="vbox-lbl">GCS</div><div class="vbox-val">{SS.v_gcs}</div></div>'
      f'</div>')

    if SS.v_pas <= 0:
        AL("PAS = 0 mmHg — Vérifier la mesure ou suspicion d'arrêt circulatoire", "danger")
    else:
        _si_val = si(SS.v_fc, SS.v_pas)
        if _si_val >= 1.5:
            AL(f"Shock Index {_si_val} ≥ 1.5 — CHOC DÉCOMPENSÉ", "danger")
        elif _si_val >= 1.0:
            AL(f"Shock Index {_si_val} ≥ 1.0 — Instabilité hémodynamique", "warning")
        else:
            st.caption(f"Shock Index : {_si_val} — Stable")

    if age < 18:
        _sv, _stxt, _salerte = sipa(SS.v_fc, age)
        AL(_stxt, "danger" if _salerte else "success")

    st.divider()

    # ── BLOC C : Douleur EVA ─────────────────────────────────────────────────
    H('<div class="card-title">😣 Douleur (EVA / NRS)</div>')
    _eva_key = WK("tr_eva")
    if _eva_key not in SS:
        SS[_eva_key] = str(int(SS.eva or 0))

    _eva_raw = st.select_slider(
        "Intensité douloureuse",
        options=[str(i) for i in range(11)],
        value=SS[_eva_key],
        key=_eva_key,
    )
    SS.eva = int(_eva_raw)
    EVA_BAR(SS.eva)

    if SS.eva >= 8:
        AL(f"EVA {SS.eva}/10 — Douleur sévère — Antalgie forte requise (piritramide / morphine)", "danger")
    elif SS.eva >= 5:
        AL(f"EVA {SS.eva}/10 — Antalgie palier 2-3 à initier", "warning")
    elif SS.eva >= 2:
        AL(f"EVA {SS.eva}/10 — Antalgie palier 1 (paracétamol)", "info")

    if SS.v_fr > 20 or SS.v_spo2 < 95:
        st.divider()
        borg_visual_scale()

    if age >= 75 or SS.v_gcs < 15:
        st.divider()
        cam_icu_visual()

    st.divider()

    # ── BLOC D : Glycémie capillaire ─────────────────────────────────────────
    H('<div class="card-title">🩸 Glycémie capillaire</div>')
    _gl_raw = st.number_input("mg/dl (0 = non mesuré)", 0, 800, 0, 5, key="tr_gl",
                               label_visibility="collapsed")
    if _gl_raw > 0:
        SS.gl = float(_gl_raw)
        _mm = round(_gl_raw / 18.016, 1)
        st.caption(f"→ {_mm} mmol/l")
        if _gl_raw < 54:
            AL(f"HYPOGLYCÉMIE SÉVÈRE {_gl_raw} mg/dl — Glucose 30 % IV IMMÉDIAT", "danger")
        elif _gl_raw < 70:
            AL(f"Hypoglycémie modérée {_gl_raw} mg/dl — Correction urgente", "warning")
        elif _gl_raw > 360:
            AL(f"Hyperglycémie sévère {_gl_raw} mg/dl — Bilan acidocétose", "danger")
        elif _gl_raw > 180:
            AL(f"Hyperglycémie {_gl_raw} mg/dl", "info")

    st.divider()

    # ── BLOC E : Motif + critères FRENCH ─────────────────────────────────────
    H('<div class="card-title">🏷️ Motif de recours</div>')
    _cat  = st.selectbox("Catégorie", list(MOTS_CAT.keys()), key="tr_cat")
    _mot  = st.selectbox("Motif principal", MOTS_CAT[_cat], key="tr_mot")
    SS.cat   = _cat
    SS.motif = _mot
    _smart_slot = st.empty()

    _det = dict(SS.det) if isinstance(SS.det, dict) else {}
    _det.update({"eva": SS.eva, "atcd": atcd, "glycemie_mgdl": SS.gl})

    _purpura_chk = st.checkbox("🔴 Purpura / pétéchies NON effaçables (test du verre)", key=WK("tr_pur"))
    _det["purpura"] = _purpura_chk
    if _purpura_chk:
        H('<div style="background:#7F1D1D;color:#FEE2E2;border-radius:10px;padding:14px;font-weight:700;margin:8px 0;animation:pulse 2s infinite;">'
          '🔴 PURPURA FULMINANS SUSPECTÉ — Ceftriaxone 2 g IV IMMÉDIAT — NE PAS ATTENDRE'
          '</div>')

    _disc_answers = {}
    if SS.motif in DISCRIMINANTS_ENRICHIS:
        H('<div class="card-title" style="margin-top:10px;">🔍 Critères discriminants FRENCH</div>')
        _disc_answers = render_discriminants_enrichis(SS.motif, key_prefix=WK("tr_disc"))
        _det_updates = process_answers(SS.motif, _disc_answers)
        _det.update(_det_updates)

    _proto = get_protocol(SS.motif)
    if _proto and _proto.get("criteria") and SS.motif not in DISCRIMINANTS_ENRICHIS:
        _selected_crit = render_discriminants(SS.motif, key=WK("tr_disc2"))
    else:
        _selected_crit = None

    SS.det = _det
    _smart = sync_clinical_context(SS)
    with _smart_slot.container():
        render_smart_alerts(_smart, show_incoherence=False)

    st.divider()

    # ── qSOFA bedside ─────────────────────────────────────────────────────────
    if age >= 16:
        _qs_fr  = int(SS.v_fr  or 16)
        _qs_gcs = int(SS.v_gcs or 15)
        _qs_pas = int(SS.v_pas or 120)
        _qs_s   = int(_qs_fr >= 22) + int(_qs_gcs < 15) + int(_qs_pas <= 100)
        _qs_col = "#EF4444" if _qs_s >= 2 else "#F59E0B" if _qs_s == 1 else "#22C55E"
        H(f'''<div style="background:{_qs_col}15;border-left:4px solid {_qs_col};
            border-radius:0 8px 8px 0;padding:7px 14px;margin:4px 0;
            display:flex;align-items:center;justify-content:space-between;">
          <div>
            <span style="font-size:.78rem;font-weight:800;color:{_qs_col};">qSOFA {_qs_s}/3</span>
            <span style="font-size:.72rem;color:#64748B;margin-left:8px;">
              {"⚠️ Sepsis suspecté — cultures + lactate + ATB < 1h" if _qs_s >= 2 else "Surveiller" if _qs_s == 1 else "Pas de sepsis suspecté"}
            </span>
          </div>
          <div style="font-size:.68rem;color:#94A3B8;text-align:right;">
            FR{"✓" if _qs_fr>=22 else "·"}&nbsp;GCS{"✓" if _qs_gcs<15 else "·"}&nbsp;PAS{"✓" if _qs_pas<=100 else "·"}
          </div>
        </div>''')

    # ── BLOC F : Validation + calcul du triage ────────────────────────────────
    _crit_err = []
    if not (20 <= (SS.v_fc or 80) <= 250):
        _crit_err.append(f"FC {SS.v_fc} bpm hors plage physiologique (20-250)")
    if not (40 <= (SS.v_pas or 120) <= 300):
        _crit_err.append(f"PAS {SS.v_pas} mmHg impossible")
    if not (50 <= (SS.v_spo2 or 98) <= 100):
        _crit_err.append(f"SpO2 {SS.v_spo2}% hors plage (50-100)")
    if not (4 <= (SS.v_fr or 16) <= 70):
        _crit_err.append(f"FR {SS.v_fr}/min impossible")
    if not (30.0 <= (SS.v_temp or 37.0) <= 44.0):
        _crit_err.append(f"T° {SS.v_temp}°C incompatible avec la vie")
    for _ce in _crit_err:
        AL(f"🚫 Valeur impossible : {_ce} — Corriger avant calcul", "danger")

    if _n2 >= NEWS2_TRI_M:
        H('''<div style="background:#7C3AED20;border:3px solid #7C3AED;border-radius:10px;
            padding:12px 16px;margin:8px 0;display:flex;align-items:center;gap:12px;">
          <div style="font-size:1.8rem;">🚨</div>
          <div style="color:#7C3AED;font-weight:800;font-size:.9rem;">
            NEWS2 {n2} ≥ {thresh} — ENGAGEMENT VITAL — APPEL MÉDECIN IMMÉDIAT
          </div>
        </div>'''.format(n2=_n2, thresh=NEWS2_TRI_M))
    elif _n2 >= 5:
        AL(f"⚠️ NEWS2 {_n2} ≥ 5 — Risque élevé — Appel médecin dans les 5 min", "warning")

    if SS.gl is not None and SS.gl < 54:
        if (SS.v_gcs or 15) <= 8:
            H('''<div style="background:#7F1D1D;color:#FEE2E2;border-radius:8px;
                padding:12px 16px;margin:6px 0;font-weight:800;font-size:.85rem;">
              🔴 COMA HYPOGLYCÉMIQUE — GCS ≤ 8 + Glycémie {gl:.0f} mg/dl
              → GLUCOSE IV IMMÉDIAT — Tri M
            </div>'''.format(gl=SS.gl))
        else:
            AL(f"🟠 Hypoglycémie sévère {SS.gl:.0f} mg/dl (< 3 mmol/l) — Glucose IV urgent", "danger")

    if age > 0:
        _sv = seuils_normaux_ped(age) if age < 16 else {
            "label": f"{int(age)} ans", "fc": (50,100), "pas": (90,140),
            "fr": (12,20), "spo2_min": 96}
        with st.expander(f"📊 Valeurs normales — {_sv['label']}", expanded=False):
            _col1, _col2, _col3, _col4 = st.columns(4)
            def _badge(val, lo, hi, unit):
                ok = lo <= val <= hi if val else True
                c  = "#22C55E" if ok else "#EF4444"
                return f'<div style="font-size:.72rem;color:{c};font-weight:700;">{val or "?"} {unit}<br><span style="color:#64748B;font-weight:400;">({lo}-{hi})</span></div>'
            _col1.markdown(_badge(SS.v_fc or 0, *_sv["fc"], "bpm"), unsafe_allow_html=True)
            _col2.markdown(_badge(SS.v_pas or 0, *_sv["pas"], "mmHg"), unsafe_allow_html=True)
            _col3.markdown(_badge(SS.v_fr or 0, *_sv["fr"], "/min"), unsafe_allow_html=True)
            _col4.markdown(f'<div style="font-size:.72rem;">SpO2 ≥ {_sv["spo2_min"]}%<br><span style="color:{"#22C55E" if (SS.v_spo2 or 98) >= _sv["spo2_min"] else "#EF4444"};font-weight:700;">{SS.v_spo2 or "?"}%</span></div>', unsafe_allow_html=True)

    if st.button("⚡ CALCULER LE TRIAGE", type="primary", use_container_width=True, key="tr_calc",
                 disabled=bool(_crit_err)):
        SS.v_news2 = _n2
        SS.niv, SS.just, SS.crit = french_triage(
            SS.motif, SS.det, SS.v_fc, SS.v_pas, SS.v_spo2,
            SS.v_fr, SS.v_gcs, SS.v_temp, age, SS.v_news2, SS.gl,
        )
        if _selected_crit:
            SS.niv, SS.just, SS.crit = apply_discriminant_selection(
                SS.niv, SS.just, SS.crit, _selected_crit)
        sync_clinical_context(SS)

    # ── RÉSULTAT — toujours visible si calculé ────────────────────────────────
    if SS.niv:
        _smart = sync_clinical_context(SS)
        if SS.motif and any(k in SS.motif.lower() for k in
                ("suicidaire","psychiatrique","intoxication")):
            H('''<div style="background:#1E3A5F;border:2px solid #3B82F6;
                border-radius:10px;padding:12px 16px;margin:8px 0;">
              <div style="font-size:.82rem;font-weight:700;color:#93C5FD;">
                🔵 Évaluation psychiatrique requise
              </div>
              <div style="font-size:.72rem;color:#94A3B8;margin-top:4px;">
                • Rester avec le patient — ne pas laisser seul<br>
                • Retirer objets dangereux / médicaments accessibles<br>
                • Ligne de crise Belgique : <strong style="color:#93C5FD;">0800 / 32.123</strong> (gratuite 24h/24)<br>
                • CBP si intoxication : <strong style="color:#93C5FD;">070 / 245.245</strong>
              </div>
            </div>''')

        if SS.v_news2 >= NEWS2_TRI_M:
            H(f'''<div style="background:linear-gradient(135deg,#7C3AED,#6D28D9);
                color:white;border-radius:12px;padding:16px 20px;margin:10px 0;
                text-align:center;box-shadow:0 0 20px #7C3AED60;
                animation:pulse 1.5s ease-in-out infinite;">
              <div style="font-size:1.4rem;font-weight:900;letter-spacing:.05em;">
                🚨 NEWS2 {SS.v_news2} — APPEL MÉDICAL IMMÉDIAT 🚨
              </div>
              <div style="font-size:.78rem;margin-top:4px;opacity:.9;">
                Engagement vital — Déchocage — Monitorage continu
              </div>
            </div>''')

        if SS.crit and 'Worst-Case' in SS.crit:
            H(f'''<div style="background:#78350F20;border-left:4px solid #F59E0B;
                border-radius:0 8px 8px 0;padding:10px 14px;margin:6px 0;">
              <div style="font-size:.72rem;font-weight:700;color:#F59E0B;">
                ⚠️ Terrain à risque — Niveau majoré automatiquement
              </div>
              <div style="font-size:.72rem;color:#94A3B8;margin-top:2px;">{SS.just}</div>
            </div>''')

        if _smart.get("triage_incoherence"):
            _ctx_no_ecg = dict(_smart)
            _ctx_no_ecg["ecg_hint"] = False
            render_smart_alerts(_ctx_no_ecg, show_incoherence=True)

        _actions_imm = []
        if SS.niv in ("M","1","2"):
            _actions_imm.append("📞 Appeler le médecin (≤ 5 min pour Tri M/1)")
            _actions_imm.append("📡 Monitorage continu — scope, SpO2, TA /5 min")
        if SS.eva >= 4:
            _actions_imm.append(f"💊 Antalgie — EVA {SS.eva}/10 → onglet Pharmacie")
        if SS.motif and any(k in SS.motif for k in ("SCA","thoracique","coronaire")):
            _actions_imm.append("❤️ ECG 18 dérivations + Troponines + Glycémie")
        if SS.motif and "AVC" in SS.motif:
            _actions_imm.append("🧠 Code Stroke — Glycémie + TDM cérébral urgent")
        if SS.motif and "purpura" in SS.motif.lower():
            _actions_imm.append("💉 Ceftriaxone 2g IV IMMÉDIAT — sans attendre")
        if _actions_imm:
            H('<div class="card-title" style="margin-top:10px;">✅ Actions immédiates</div>')
            for _act_i, _act in enumerate(_actions_imm):
                st.checkbox(_act, key=WK(f"act_{_act_i}"))

        _css = TCSS.get(SS.niv, "tri-3B")
        _hero_extra = " smart-incoherence" if _smart.get("triage_incoherence") else ""
        _lbl = LABELS.get(SS.niv, f"TRI {SS.niv}")
        _sec = SECTEURS.get(SS.niv, "À définir")
        _del = DELAIS.get(SS.niv, 60)
        H(f'<div class="tri-hero triage-result-sticky {_css}{_hero_extra}">'
          f'<div class="tri-hero-level">{_lbl}</div>'
          f'<div class="tri-hero-just">{SS.just}</div>'
          f'<div class="tri-hero-meta">'
          f'<span class="tri-meta-chip">📍 {_sec}</span>'
          f'<span class="tri-meta-chip">⏱ Délai ≤ {_del} min</span>'
          f'<span class="tri-meta-chip">NEWS2 {SS.v_news2}</span>'
          f'</div></div>')

        _D, _A = verifier_coherence(
            SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr,
            SS.v_gcs, SS.v_temp, SS.eva, SS.motif,
            atcd, SS.det, SS.v_news2, SS.gl, age, SS.niv or "")
        for d in _D: AL(d, "danger")
        for a in _A: AL(a, "warning")

        render_next_steps(SS, WK("next"))

        st.divider()

        _si_txt  = f"{_si_val}"
        _gl_txt  = f"{SS.gl:.0f} mg/dl ({SS.gl/18.016:.1f} mmol/l)" if SS.gl else "Non mesurée"
        _atcd_txt = ", ".join(atcd) if atcd else "Aucun"
        _now_txt  = datetime.now().strftime("%d/%m/%Y à %H:%M")
        _synt = (
            f"SYNTHÈSE IAO — {_now_txt}\n"
            f"Op. : {SS.op or 'IAO'} | Session : {SS.uid_cur or '—'}\n"
            f"{'═'*50}\n"
            f"TRIAGE  : {SS.niv} — {_lbl}\n"
            f"Raison  : {SS.just}\n"
            f"Secteur : {_sec} | Délai médecin ≤ {_del} min\n"
            f"Motif   : {SS.motif} ({SS.cat})\n"
            f"EVA     : {SS.eva}/10\n"
            f"{'─'*50}\n"
            f"FC {SS.v_fc} | PAS {SS.v_pas} | SpO2 {SS.v_spo2}%\n"
            f"FR {SS.v_fr} | T° {SS.v_temp}°C | GCS {SS.v_gcs}/15\n"
            f"Shock Index {_si_txt} | NEWS2 {SS.v_news2}\n"
            f"Glycémie : {_gl_txt}\n"
            f"{'─'*50}\n"
            f"ATCD   : {_atcd_txt}\n"
            f"Allergie: {alg or 'aucune'}\n"
            f"O₂     : {'OUI' if o2 else 'Non'}\n"
            f"{'═'*50}\n"
            f"FRENCH V1.1 | BCFI Belgique — Ismail Ibn-Daifa — AKIR-IAO v20"
        )

        with st.expander("📋 Synthèse IAO — Copier / Télécharger", expanded=False):
            st.code(_synt, language=None)
            st.download_button("📥 Télécharger (.txt)", data=_synt,
                file_name=f"IAO_{datetime.now().strftime('%Y%m%d_%H%M')}_Tri{SS.niv}.txt",
                mime="text/plain", use_container_width=True)

        _sv1, _sv2 = st.columns(2)
        if _sv1.button("💾 Enregistrer patient", use_container_width=True, key="tr_save"):
            _uid = enregistrer_patient({
                "motif": SS.motif, "cat": SS.cat, "niv": SS.niv,
                "n2": SS.v_news2, "fc": SS.v_fc, "pas": SS.v_pas,
                "spo2": SS.v_spo2, "fr": SS.v_fr, "temp": SS.v_temp,
                "gcs": SS.v_gcs, "op": SS.op,
            })
            SS.uid_cur = _uid; SS.t_reev = datetime.now()
            SS.histo.insert(0, {"uid": _uid, "h": datetime.now().strftime("%H:%M"),
                                 "motif": SS.motif, "niv": SS.niv, "n2": SS.v_news2})
            st.success(f"✅ Enregistré — UID : {_uid}")

        if _sv2.button("📡 SBAR rapide", use_container_width=True, key="tr_sbar"):
            SS["show_sbar"] = True

        if SS.get("show_sbar"):
            _sbar = build_sbar(age, SS.motif, SS.cat, atcd, alg, o2,
                SS.v_temp, SS.v_fc, SS.v_pas, SS.v_spo2, SS.v_fr, SS.v_gcs,
                SS.eva, SS.v_news2, SS.niv, SS.just, SS.crit,
                SS.op or "IAO", SS.gl)
            SBAR_RENDER(_sbar, key_suffix="_triage")
