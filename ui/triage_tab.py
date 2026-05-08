# ui/triage_tab.py — Onglet Triage — AKIR-IAO v20
# Logique extraite de streamlit_app.py T[1] (modularisation)
from __future__ import annotations
import streamlit as st
from datetime import datetime

from config import NEWS2_TRI_M, DELAIS, LABELS, SECTEURS, TCSS
from clinical.news2 import (
    calculer_news2,
    pews_meta, seuils_normaux_ped,
    calculer_pews as calculer_pews_vitaux,
)
from clinical.triage import french_triage, verifier_coherence
from clinical.vitaux import si, sipa
from clinical.french_v12 import (
    FRENCH_MOTS_CAT,
    get_protocol, render_discriminants, apply_discriminant_selection,
    DISCRIMINANTS_ENRICHIS, render_discriminants_enrichis, process_answers,
)
from persistence.registry import enregistrer_patient
from akir_iao_enhancements import gcs_visual_scale, borg_visual_scale, cam_icu_visual
from ui.components import H, AL, EVA_BAR, SBAR_RENDER, build_sbar

MOTS_CAT = FRENCH_MOTS_CAT


@st.cache_data(ttl=60, show_spinner=False)
def _calc_news2_triage(fr, spo2, o2, temp, pas, fc, gcs, bpco):
    n2, _ = calculer_news2(fr, spo2, o2, temp, pas, fc, gcs, bpco)
    return n2


def _wk(base: str, scope: str | None = None) -> str:
    SS = st.session_state
    parts = [str(SS.get("uid") or SS.get("sid") or "s")]
    if scope:
        parts.append(str(scope))
    parts.append(str(base))
    return "__".join(p.replace(" ", "_") for p in parts if p)


def render() -> None:
    SS = st.session_state
    WK = _wk

    age   = float(SS.get("age") or 45)
    poids = float(SS.get("poids") or 70)
    atcd  = list(SS.get("atcd") or [])
    alg   = str(SS.get("alg") or "")
    o2    = bool(SS.get("o2") or False)
    _si_val = 0.0  # valeur par défaut si PAS <= 0

    def _n2_compute() -> int:
        n2 = _calc_news2_triage(
            SS.v_fr, SS.v_spo2, SS.o2,
            SS.v_temp, SS.v_pas, SS.v_fc, SS.v_gcs, SS.v_bpco)
        SS.v_news2 = n2
        return n2

    # ── BLOC A : Chronomètre tactile ─────────────────────────────────────────
    _ta1, _ta2 = st.columns(2)
    if _ta1.button("⏱ Marquer arrivée", key="tr_arr", use_container_width=True):
        SS.t_arr = datetime.now(); SS.histo = []; SS.reevs = []
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

    SS.v_bpco = st.checkbox("BPCO — utiliser SpO2 cible 88-92 %", key=WK("tr_bp"),
                             value=bool(SS.v_bpco or "BPCO" in atcd))
    if SS.v_bpco:
        AL("BPCO actif — SpO2 > 96 % sous O₂ = RISQUE hypercapnie", "warning")

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

    # ── RÉSULTAT — toujours visible si calculé ────────────────────────────────
    if SS.niv:
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
        _lbl = LABELS.get(SS.niv, f"TRI {SS.niv}")
        _sec = SECTEURS.get(SS.niv, "À définir")
        _del = DELAIS.get(SS.niv, 60)
        H(f'<div class="tri-hero {_css}">'
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
