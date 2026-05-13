# ui/pharmacie_tab.py — Onglet Pharmacie — AKIR-IAO v20
# Logique extraite de streamlit_app.py T[2] (modularisation)
from __future__ import annotations
import pandas as pd
import streamlit as st
from datetime import datetime

from clinical.pharmaco import (
    paracetamol, naproxene, ketorolac, diclofenac, tramadol, piritramide, morphine,
    naloxone, adrenaline, glucose, ceftriaxone, litican,
    salbutamol, furosemide, ondansetron,
    sepsis_bundle_1h, ketamine_intranasale,
    midazolam_im, protocole_epilepsie_ped,
    poids_dosage_opioides, crise_hypertensive,
    generer_etiquette, check_safety, PROTOCOLES_IAO,
)
from clinical.perfusion import (
    perf_morphine, perf_piritramide, perf_ketamine,
    perf_midazolam, perf_adrenaline, perf_noradrenaline,
    perf_insuline, perf_amiodarone, perf_labetalol,
    perf_magnesium, perf_nicardipine, perf_dobutamine,
    calculer_debit, convertir_debit,
)
from clinical.compatibility import check_iv_compatibility, med_from_perfusion_choice
from akir_iao_enhancements import (
    section_dilutions_hainaut, calculateur_noradrenaline,
    section_fiches_medicaments,
)
from clinical.pharmaco_rea import (
    search_dilutions, get_compatibilites, get_substances_list,
    check_compatibility, get_all_compat_for, get_partner,
)
from ui.components import H, AL
from ui.explainer import explain


def _wk(base: str, scope: str | None = None) -> str:
    SS = st.session_state
    parts = [str(SS.get("uid") or SS.get("sid") or "s")]
    if scope:
        parts.append(str(scope))
    parts.append(str(base))
    return "__".join(p.replace(" ", "_") for p in parts if p)


def _render_rea_database(WK) -> None:
    """Rendu de la base REA, isolé pour rester dans l'onglet Perfusions IV."""
    st.divider()
    H('<div class="card-title">🏥 Base de données REA — Hainaut v20</div>')

    _all_dils = search_dilutions("")
    with st.expander(
        f"📋 Dilutions IV continues — {len(_all_dils)} molécules (protocole REA)",
        expanded=False,
    ):
        st.caption(
            "Source : Protocole dilutions standardisées intraveineuses continues "
            "avec adaptation au marché pharmaceutique belge (BCFI/AFMPS). "
            "⚠️ Les flags « check_protocol » signalent des discordances ou points à valider localement."
        )
        _rc1, _rc2 = st.columns([4, 1])
        _rea_q = _rc1.text_input(
            "Rechercher",
            placeholder="ex : noradrénaline, midazolam, héparine…",
            key=WK("rea_search"),
            label_visibility="collapsed",
        )
        _rea_flags_only = _rc2.checkbox("⚠️ Flags seul.", key=WK("rea_flags"))

        _dils = search_dilutions(_rea_q) if _rea_q else _all_dils
        if _rea_flags_only:
            _dils = [d for d in _dils if d.get("check_protocol")]

        if not _dils:
            st.info("Aucun résultat — essayer un autre terme")
        else:
            for _d in _dils:
                _dil = _d.get("dilution", {})
                _conc = _dil.get("concentration_finale", {})
                _flag = _d.get("check_protocol", False)
                _corr = _d.get("correction_manuscrite")
                _flag_pfx = "⚠️ " if _flag else ""
                _conc_value = _conc.get("valeur", "?")
                _conc_unit = _conc.get("unite", "")
                _conc_str = f"{_conc_value} {_conc_unit}".strip()
                _title = (
                    f"{_flag_pfx}{_d.get('nom_source', 'Molécule inconnue')} — "
                    f"{_d.get('DCI', 'DCI ?')} — {_conc_str}"
                )
                with st.expander(_title, expanded=False):
                    _da, _db = st.columns(2)
                    with _da:
                        st.markdown("**Dilution**")
                        if _dil.get("description_source"):
                            st.caption(_dil["description_source"])
                        if _dil.get("volume_total_ml"):
                            st.caption(
                                f"Vol. total : {_dil['volume_total_ml']} ml  |  "
                                f"Diluant : {_dil.get('diluant', '?')}"
                            )
                        if _dil.get("mode"):
                            st.caption(f"Mode : {_dil['mode']}")
                        if _d.get("conservation"):
                            st.caption(f"🌡 {_d['conservation']}")
                    with _db:
                        st.markdown("**Adaptation belge**")
                        _be = _d.get("adaptation_belge", {})
                        if not isinstance(_be, dict):
                            _be = {}
                        _noms = _be.get("noms_commerciaux_be", [])
                        if _noms:
                            st.caption("BE : " + " | ".join(_noms[:2]))
                        if _be.get("presentation_ampoule_be"):
                            st.caption(_be["presentation_ampoule_be"])
                        _val = _be.get("validation_dosage", "")
                        if _val:
                            _vic = (
                                "🟢" if "conforme" in _val.lower()
                                else "🔴" if "non" in _val.lower()
                                else "🟡"
                            )
                            st.caption(f"{_vic} {_val}")
                        if _be.get("remarque"):
                            st.caption(_be["remarque"])

                    if _flag:
                        st.warning(
                            f"⚠️ CHECK PROTOCOL : "
                            f"{_d.get('flag_check_protocol_raison', '')}"
                        )
                    if _corr:
                        st.info(f"📝 Correction manuscrite : {_corr}")

                    _calc = _conc.get("calcul") or _conc.get("note") or ""
                    if _calc:
                        st.caption(f"Calcul : {_calc}")

    _compat_count = len(get_compatibilites())
    with st.expander(
        f"🔬 Compatibilité en Y — Tableau HUG ({_compat_count} paires)",
        expanded=False,
    ):
        st.caption(
            "Source : Pharmacie des HUG (Hôpitaux Universitaires de Genève) — "
            "HUG_CompatAdm_DCI.xlsx, révision 10.08.2018. "
            "Compatibilité valable par paires uniquement. "
            "C* = compatible sous conditions (lire la précision)."
        )
        _subs = get_substances_list()
        _cc1, _cc2 = st.columns(2)
        _sub_a = _cc1.selectbox(
            "Substance A", ["— choisir —"] + _subs, key=WK("compat_a")
        )
        _sub_b = _cc2.selectbox(
            "Substance B", ["— choisir —"] + _subs, key=WK("compat_b")
        )

        if _sub_a != "— choisir —" and _sub_b != "— choisir —":
            if _sub_a == _sub_b:
                st.info("Sélectionner deux substances différentes")
            else:
                _res = check_compatibility(_sub_a, _sub_b)
                if _res:
                    _st = _res.get("statut", "?")
                    _pal = {
                        "C": "#22C55E",
                        "C*": "#F59E0B",
                        "I": "#EF4444",
                    }.get(_st, "#94A3B8")
                    _lbl = {
                        "C": "✅ COMPATIBLE",
                        "C*": "⚠️ COMPATIBLE — sous conditions",
                        "I": "🚫 INCOMPATIBLE",
                    }.get(_st, _st)
                    H(
                        f"<div style='background:{_pal}18;border:2px solid {_pal};"
                        f"border-radius:12px;padding:16px;text-align:center;margin:8px 0;'>"
                        f"<div style='font-size:.7rem;color:#94A3B8;'>"
                        f"{_res.get('substance_A', '?')} × {_res.get('substance_B', '?')}</div>"
                        f"<div style='font-size:1.6rem;font-weight:900;color:{_pal};"
                        f"margin:4px 0;'>{_lbl}</div>"
                        f"<div style='font-size:.7rem;color:{_pal};'>"
                        f"Réf. {_res.get('reference','?')} — "
                        f"HUG_CompatAdm_DCI 2018</div></div>"
                    )
                    if _res.get("precision"):
                        (st.warning if _st in ("C*", "I") else st.info)(
                            _res["precision"]
                        )
                else:
                    H(
                        "<div style='background:#1E293B;border:2px solid #475569;"
                        "border-radius:12px;padding:16px;text-align:center;margin:8px 0;'>"
                        "<div style='font-size:1rem;font-weight:700;color:#94A3B8;'>"
                        "Aucune donnée disponible pour cette paire</div>"
                        "<div style='font-size:.72rem;color:#64748B;margin-top:4px;'>"
                        "Contacter l'assistance pharmaceutique — CBP 070/245.245</div>"
                        "</div>"
                    )

        if _sub_a != "— choisir —":
            _all_for_a = get_all_compat_for(_sub_a)
            if _all_for_a:
                with st.expander(
                    f"Toutes les compatibilités connues pour {_sub_a} "
                    f"({len(_all_for_a)} entrées)",
                    expanded=False,
                ):
                    _rows = []
                    for _e in _all_for_a:
                        _pname, _pdci = get_partner(_e, _sub_a)
                        _st_e = _e.get("statut", "?")
                        _ic = "✅" if _st_e == "C" else "⚠️" if _st_e == "C*" else "🚫"
                        _rows.append({
                            "Partenaire": _pname,
                            "DCI": _pdci,
                            "Statut": f"{_ic} {_st_e}",
                            "Précision": _e.get("precision") or "",
                            "Réf.": _e.get("reference", ""),
                        })
                    st.dataframe(
                        pd.DataFrame(_rows),
                        use_container_width=True,
                        hide_index=True,
                    )

        st.caption(
            "⚠️ Données issues de tests par paires — pas de données disponibles "
            "pour les associations de plus de 2 médicaments. "
            "En cas de doute : CBP 070/245.245 (24h/24)."
        )


def render() -> None:
    SS = st.session_state
    WK = _wk

    age         = float(SS.get("age") or 45)
    poids       = float(SS.get("poids") or 70)
    taille      = float(SS.get("taille") or 170)
    atcd        = list(SS.get("atcd") or [])
    atcd_checks = dict(SS.get("atcd_checks") or {})
    trt_checks  = dict(SS.get("trt_checks") or {})

    _gl_ph = (SS.det.get("glycemie_mgdl") if isinstance(SS.det, dict) else None) or SS.gl
    _dose_mode = "mg/kg" if age < 15 else "adulte"

    _poids_eff, _pit_note = poids_dosage_opioides(poids, taille,
        "H" if SS.get("pt_sex","Non précisé") == "Masculin" else "F")
    _pit_label = f" — opioïdes : {_poids_eff:.0f} kg (PIT)" if _pit_note else ""
    _pv_alerts = [
        trt_checks.get("IMAO (inhibiteurs MAO)"),
        atcd_checks.get("Insuffisance rénale chronique"),
        trt_checks.get("Anticoagulants/AOD"),
    ]
    _pv_alert_label = f"⚠️ {sum(bool(a) for a in _pv_alerts)} alerte(s)" if any(_pv_alerts) else "✅ Pas d'alerte PV"
    H(f'<div style="background:linear-gradient(135deg,#004A99,#0069D9);color:#fff;'
      f'border-radius:10px;padding:10px 14px;margin-bottom:10px;display:flex;'
      f'justify-content:space-between;align-items:center;">'
      f'<div><div style="font-size:.72rem;opacity:.75;">Doses pour</div>'
      f'<div style="font-size:1.1rem;font-weight:800;">{poids:.0f} kg — {age:.0f} ans{_pit_label}'
      f' <span style="font-size:.75rem;opacity:.7;">({_dose_mode})</span></div></div>'
      f'<div style="text-align:right;font-size:.7rem;opacity:.8;">'
      f'{_pv_alert_label}'
      f'</div></div>')
    if _pit_note:
        AL(f"Obésité — {_pit_note}", "warning")

    if trt_checks.get("IMAO (inhibiteurs MAO)"):
        H('<div class="pharma-alert-bar">🔴 IMAO — Tramadol CONTRE-INDIQUÉ ABSOLU</div>')
    if atcd_checks.get("Insuffisance rénale chronique"):
        H('<div class="pharma-alert-bar">🔴 Insuff. rénale — AINS tous CONTRE-INDIQUÉS</div>')
    if trt_checks.get("Anticoagulants/AOD"):
        AL("Anticoagulants en cours — Vigilance hémorragique renforcée", "warning")
    if SS.niv in ("M", "1", "2") and SS.eva >= 7:
        H(f'<div style="background:#78350F;color:#FDE68A;border-radius:8px;padding:10px;font-weight:700;margin:6px 0;">'
          f'⚠️ TRI {SS.niv} — EVA {SS.eva}/10 — ANTALGIE FORTE PRIORITAIRE (piritramide/morphine)</div>')
    if SS.get("pharmacie_auto_antalgie"):
        with st.expander("🚨 Antalgie prioritaire — dictée clinique EVA ≥ 7", expanded=True):
            AL(SS.get("pharmacie_auto_antalgie_reason") or "Douleur sévère détectée par la dictée.", "danger")
            st.caption("L'onglet Antalgiques ci-dessous est à prioriser; doses calculées avec le poids patient synchronisé.")

    with st.expander("ℹ️ Comprendre la pharmacologie d'urgence", expanded=False):
        _e1, _e2 = st.columns(2)
        with _e1:
            explain("eva")
            explain("opioides_conversion")
            explain("poids_ideal")
            explain("5b")
        with _e2:
            explain("anaphylaxie")
            explain("hypoglycemie")
            explain("sepsis_bundle")
            explain("aod")

    # ── Raccourcis médicaments ─────────────────────────────────────────────────
    H('<div class="card-title">⚡ Raccourcis — Doses immédiates</div>')
    _rq1, _rq2, _rq3 = st.columns(3)
    _rq4, _rq5, _rq6 = st.columns(3)
    for _col, _name, _fn, _args in [
        (_rq1, "Para IV",     paracetamol,  (poids, age, atcd)),
        (_rq2, "Adrénaline",  adrenaline,   (poids, atcd)),
        (_rq3, "Ceftriaxone", ceftriaxone,  (poids, age, atcd)),
        (_rq4, "Morphine",    morphine,      (poids, age, atcd)),
        (_rq5, "Ondansétron", ondansetron,  (poids, age, atcd)),
        (_rq6, "Naloxone",    naloxone,     (poids, age, False, atcd)),
    ]:
        if _col.button(_name, key=WK(f"rq_{_name}"), use_container_width=True):
            _rx, _re = _fn(*_args)
            if _re: AL(_re, "danger")
            elif _rx:
                _dose_txt = (
                    f"{_rx.get('dose_g',_rx.get('dose_mg',_rx.get('dose','?')))} — {_rx.get('admin',_rx.get('voie',''))}"
                )
                st.toast(f"✅ {_name} : {_dose_txt}", icon="💊")

    # ── Protocoles IAO anticipés ───────────────────────────────────────────────
    if SS.motif and SS.motif in PROTOCOLES_IAO:
        st.divider()
        H(f'<div class="card-title">🚑 Protocoles anticipés IAO — {SS.motif}</div>')
        for _proto_iao in PROTOCOLES_IAO[SS.motif]:
            _cond = _proto_iao.get("condition", lambda v: True)
            try:
                _show = _cond({"pas": SS.v_pas, "spo2": SS.v_spo2, "fc": SS.v_fc})
            except Exception:
                _show = True
            if not _show:
                continue
            _dose_iao = _proto_iao.get("dose") or ""
            if not _dose_iao and _proto_iao.get("dose_fn"):
                try: _dose_iao = _proto_iao["dose_fn"](poids)
                except Exception: _dose_iao = "?"
            AL(f"{_proto_iao['med']} : {_dose_iao} ({_proto_iao.get('voie','?')})", "info")

    # ── Vérifications sécurité ─────────────────────────────────────────────────
    for _med_chk in ["Tramadol", "Morphine", "AINS", "Midazolam"]:
        for _sa in check_safety(_med_chk, {"atcd": atcd}, {"age": age, "poids": poids}):
            AL(_sa["message"], _sa["niveau"])

    st.divider()

    _ph_labels = [
        "Antalgiques", "Urgences vitales", "Infectiologie",
        "Cardio/Respi", "Pédiatrie", "🧪 Perfusions IV",
    ]
    if age >= 18:
        _ph_labels[4] = "▫️ Pédiatrie"
    _PH = st.tabs(_ph_labels)

    # ── Antalgiques ───────────────────────────────────────────────────────────
    with _PH[0]:
        H('<div class="card-title">Palier 1 — Non opioïdes</div>')
        _pc1, _pc2 = st.columns(2)

        with _pc1:
            _p, _pe = paracetamol(poids, age, atcd)
            if _pe: AL(_pe, "danger")
            else:
                _dose_p = (_p or {}).get("dose_display", f"{(_p or {}).get('dose_mg',1000):.0f} mg")
                H(f'<div class="rx-compact"><div class="rx-compact-dose">{_dose_p}</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Paracétamol IV (Perfalgan)</div>'
                  f'<div class="rx-compact-detail">{(_p or {}).get("admin","")} — {(_p or {}).get("note","")}</div>'
                  f'<div class="rx-compact-detail" style="color:#64748B;font-style:italic;">{(_p or {}).get("ref","")}</div></div></div>')

        with _pc2:
            _n, _ne = naproxene(poids, age, atcd)
            if _ne: H(f'<div class="rx-compact"><div class="rx-compact-dose" style="color:#EF4444;">🔒</div>'
                       f'<div class="rx-compact-info"><div class="rx-compact-name">Naproxène PO</div>'
                       f'<div class="rx-compact-detail" style="color:#EF4444;">{_ne}</div></div></div>')
            else:
                H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_n or {}).get("dose_mg",500):.0f} mg</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Naproxène PO</div>'
                  f'<div class="rx-compact-detail">{(_n or {}).get("admin","")} — {(_n or {}).get("note","")}</div></div></div>')

        _pc3, _pc4 = st.columns(2)
        with _pc3:
            _k, _ke = ketorolac(poids, age, atcd)
            if _ke: H(f'<div class="rx-compact"><div class="rx-compact-dose" style="color:#EF4444;">🔒</div>'
                       f'<div class="rx-compact-info"><div class="rx-compact-name">Taradyl® IM</div>'
                       f'<div class="rx-compact-detail" style="color:#EF4444;">{_ke}</div></div></div>')
            else:
                H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_k or {}).get("dose_mg",30):.0f} mg IM</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Taradyl® (Kétorolac) IM</div>'
                  f'<div class="rx-compact-detail">{(_k or {}).get("admin","")} — {(_k or {}).get("note","")}</div></div></div>')

        with _pc4:
            _d, _de = diclofenac(poids, age, atcd)
            if _de: H(f'<div class="rx-compact"><div class="rx-compact-dose" style="color:#EF4444;">🔒</div>'
                       f'<div class="rx-compact-info"><div class="rx-compact-name">Voltarène® IM</div>'
                       f'<div class="rx-compact-detail" style="color:#EF4444;">{_de}</div></div></div>')
            else:
                H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_d or {}).get("dose_mg",75):.0f} mg IM</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Voltarène® (Diclofénac) IM</div>'
                  f'<div class="rx-compact-detail">{(_d or {}).get("admin","")} — {(_d or {}).get("note","")}</div></div></div>')

        st.divider()
        H('<div class="card-title">Palier 2 — Opioïdes faibles</div>')
        _tr, _tre = tramadol(poids, age, atcd)
        if _tre: AL(_tre, "danger" if "contre" in _tre.lower() else "warning")
        else:
            H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_tr or {}).get("dose_mg",50):.0f} mg</div>'
              f'<div class="rx-compact-info"><div class="rx-compact-name">Tramadol (Tradonal®)</div>'
              f'<div class="rx-compact-detail">{(_tr or {}).get("admin","")} — {(_tr or {}).get("note","")}</div></div></div>')

        st.divider()
        H('<div class="card-title">Palier 3 — Opioïdes forts</div>')
        _di, _die = piritramide(poids, age, atcd)
        if not _die:
            for _ma, _mc in (_di or {}).get("alerts",[]): AL(_ma, _mc)
            H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_di or {}).get("dose_min",0):.1f}–{(_di or {}).get("dose_max",0):.1f} mg IV</div>'
              f'<div class="rx-compact-info"><div class="rx-compact-name">Dipidolor® (Piritramide) IV</div>'
              f'<div class="rx-compact-detail">{(_di or {}).get("admin","")} — {(_di or {}).get("note","")}</div></div></div>')
        _mo, _moe = morphine(poids, age, atcd)
        if not _moe:
            for _ma, _mc in (_mo or {}).get("alerts",[]): AL(_ma, _mc)
            H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_mo or {}).get("dose_min",0):.1f}–{(_mo or {}).get("dose_max",0):.1f} mg IV</div>'
              f'<div class="rx-compact-info"><div class="rx-compact-name">Morphine IV titrée</div>'
              f'<div class="rx-compact-detail">{(_mo or {}).get("admin","")} — {(_mo or {}).get("note","")}</div></div></div>')

        st.divider()
        H('<div class="card-title">Antispasmodique</div>')
        _li, _lie = litican(poids, age, atcd)
        if not _lie:
            H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_li or {}).get("dose_mg",40):.0f} mg IM</div>'
              f'<div class="rx-compact-info"><div class="rx-compact-name">Litican® IV/IM (Alizapride)</div>'
              f'<div class="rx-compact-detail">{(_li or {}).get("voie","")} — {(_li or {}).get("dose_note","")}</div></div></div>')

    # ── Urgences vitales ──────────────────────────────────────────────────────
    with _PH[1]:
        H('<div class="card-title">Urgences vitales — Doses immédiates</div>')

        _ar, _are = adrenaline(poids, atcd)
        if not _are:
            H(f'<div class="rx-compact urgent"><div class="rx-compact-dose">{(_ar or {}).get("dose_mg",0.5)} mg IM</div>'
              f'<div class="rx-compact-info"><div class="rx-compact-name">Adrénaline IM (Sterop 1 mg/ml)</div>'
              f'<div class="rx-compact-detail">{(_ar or {}).get("voie","")} — {(_ar or {}).get("rep","")}</div></div></div>')

        if _gl_ph is not None:
            _gr, _gre = glucose(poids, _gl_ph, atcd)
            if not _gre:
                H(f'<div class="rx-compact urgent"><div class="rx-compact-dose">{(_gr or {}).get("dose_g",0)} g IV</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Glucose 30 % IV</div>'
                  f'<div class="rx-compact-detail">{(_gr or {}).get("vol","")} — {(_gr or {}).get("ctrl","")}</div></div></div>')
        else:
            H('<div class="rx-compact" style="opacity:.5;"><div class="rx-compact-dose">?</div>'
              '<div class="rx-compact-info"><div class="rx-compact-name">Glucose 30 % IV</div>'
              '<div class="rx-compact-detail">Mesurer la glycémie d\'abord</div></div></div>')

        _dep_ph = st.checkbox("Patient dépendant aux opioïdes (naloxone titrée)", key=WK("ph_dep2"))
        _nr, _ = naloxone(poids, age, _dep_ph, atcd)
        if _nr:
            H(f'<div class="rx-compact urgent"><div class="rx-compact-dose">{(_nr or {}).get("dose",0.4)} mg IV</div>'
              f'<div class="rx-compact-info"><div class="rx-compact-name">Naloxone IV (Narcan®)</div>'
              f'<div class="rx-compact-detail">{(_nr or {}).get("admin","")}</div></div></div>')
            if st.checkbox("✅ Naloxone administrée — Activer rappel re-narcose", key=WK("nalox_done")):
                SS["nalox_time"] = datetime.now()
                st.toast("⏱ Rappel réévaluation naloxone programmé (15 et 30 min)", icon="⚠️")
        if SS.get("nalox_time"):
            _mins_post_nalox = (datetime.now() - SS["nalox_time"]).total_seconds() / 60
            if 13 <= _mins_post_nalox <= 20:
                H('<div style="background:#7F1D1D;color:#FEE2E2;border-radius:10px;padding:14px 16px;'
                  'margin:8px 0;font-weight:800;font-size:.85rem;animation:pulse 1s infinite;">'
                  f'🔴 RE-NARCOSE POSSIBLE — {_mins_post_nalox:.0f} min post-naloxone<br>'
                  '<span style="font-weight:400;font-size:.75rem;">RÉÉVALUER FR / GCS / SpO2 MAINTENANT (demi-vie naloxone < morphine)</span>'
                  '</div>')
            elif 28 <= _mins_post_nalox <= 35:
                AL(f"⚠️ 30 min post-naloxone — Réévaluation obligatoire FR / GCS / SpO2", "warning")

        st.divider()
        H('<div class="card-title">🦠 Sepsis bundle 1h — SSC 2021</div>')
        st.caption("Surviving Sepsis Campaign 2021 — Evans L et al.")
        if SS.v_news2 >= 5 or (SS.motif and "sepsis" in SS.motif.lower()):
            AL("⚠️ qSOFA ≥ 2 ou NEWS2 ≥ 5 — Sepsis à exclure activement", "warning")
        _sep_actions = [
            ("Lactate ≥ 2 mmol/L : hémocultures × 2 avant ABX", "hemo"),
            ("ABX large spectre IV dans les 60 min", "abx"),
            ("Remplissage NaCl 0,9% ou Ringer 30 ml/kg si PAS < 90", "vol"),
            ("Noradrénaline si PAM < 65 mmHg après remplissage", "nora"),
            ("Oxygène cible SpO2 92-96%", "o2"),
        ]
        if "sep_times" not in SS: SS["sep_times"] = {}
        for _sa_label, _sa_key in _sep_actions:
            _sc1, _sc2 = st.columns([5,2])
            _done = _sc1.checkbox(_sa_label, key=WK(f"sep_{_sa_key}"))
            if _done and _sa_key not in SS["sep_times"]:
                SS["sep_times"][_sa_key] = datetime.now()
            if _done and _sa_key in SS["sep_times"]:
                _dt = (datetime.now() - SS["sep_times"][_sa_key]).total_seconds()
                _dm, _ = divmod(int(_dt), 60)
                _sc2.caption(f"✅ il y a {_dm} min")
        _sblact = st.number_input("Lactate (mmol/l, 0=non dosé)", 0.0, 20.0, 0.0, 0.1, key="ph_sblact")
        _sb = sepsis_bundle_1h(SS.v_pas or 120, _sblact or None, SS.v_temp, SS.v_fc, poids, atcd) or {}
        if _sb.get("choc_septique"):
            AL("CHOC SEPTIQUE — Réanimation immédiate", "danger")
        for _ml, _md, _mc in _sb.get("checklist", []):
            H(f'<div class="al {_mc}" style="padding:6px 12px;margin:2px 0;">'
              f'<input type="checkbox" style="margin-right:8px;"><strong>{_ml}</strong> — {_md}</div>')

        st.divider()
        H('<div class="card-title">Acide tranexamique IV</div>')
        H('<div class="rx-compact urgent"><div class="rx-compact-dose">1 g IV</div>'
          '<div class="rx-compact-info"><div class="rx-compact-name">Acide tranexamique (CRASH-2)</div>'
          '<div class="rx-compact-detail">En 10 min — Efficace < 3h post-trauma — puis 1 g/8h</div></div></div>')

    # ── Infectiologie ─────────────────────────────────────────────────────────
    with _PH[2]:
        H('<div class="card-title">Antibiotiques urgents</div>')
        _cf, _cfe = ceftriaxone(poids, age, atcd)
        if not _cfe:
            H(f'<div class="rx-compact urgent"><div class="rx-compact-dose">{(_cf or {}).get("dose_g",2)} g IV</div>'
              f'<div class="rx-compact-info"><div class="rx-compact-name">Ceftriaxone IV (Rocéphine®)</div>'
              f'<div class="rx-compact-detail">{(_cf or {}).get("admin","")} — {(_cf or {}).get("note","")}</div></div></div>')

        st.divider()
        H('<div class="card-title">Crise hypertensive — Cibles par étiologie</div>')
        AL("Ne jamais normaliser trop rapidement — risque ischémique cérébral", "warning")
        _ctx_hta = st.selectbox("Étiologie HTA", [
            "Urgence hypertensive standard", "AVC ischémique (non thrombolysé)",
            "AVC ischémique (si thrombolyse)", "AVC hémorragique",
            "Dissection aortique", "OAP hypertensif",
        ], key="ph_ctx_hta2")
        _chp, _che = crise_hypertensive(SS.v_pas or 120, _ctx_hta, poids, atcd)
        if _che: AL(_che, "danger")
        else:
            AL(f"Cible : {(_chp or {}).get('cible','À confirmer')}", "warning")

    # ── Cardio / Respi ────────────────────────────────────────────────────────
    with _PH[3]:
        H('<div class="card-title">Bronchospasme</div>')
        _grav2 = st.select_slider("Gravité bronchospasme", ["legere","moderee","severe"], "moderee",
            key=WK("ph_grav2"),
            format_func=lambda x: {"legere":"Légère","moderee":"Modérée","severe":"Sévère"}[x])
        _sr, _se = salbutamol(poids, age, _grav2, atcd)
        if not _se:
            H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_sr or {}).get("dose_mg",2.5)} mg</div>'
              f'<div class="rx-compact-info"><div class="rx-compact-name">Salbutamol nébulisation (Ventolin®)</div>'
              f'<div class="rx-compact-detail">{(_sr or {}).get("dilution","")} — {(_sr or {}).get("debit_o2","")}</div></div></div>')

        st.divider()
        H('<div class="card-title">OAP / Diurèse</div>')
        _fu, _fue = furosemide(poids, age, atcd)
        if not _fue:
            H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_fu or {}).get("dose_min",40):.0f}–{(_fu or {}).get("dose_max",80):.0f} mg IV</div>'
              f'<div class="rx-compact-info"><div class="rx-compact-name">Furosémide IV (Lasix®)</div>'
              f'<div class="rx-compact-detail">IV lent en 2-5 min</div></div></div>')

    # ── Pédiatrie ─────────────────────────────────────────────────────────────
    with _PH[4]:
        if age >= 18:
            AL("Cet onglet est réservé aux patients < 18 ans", "info")
        else:
            H(f'<div class="card-title">EME Pédiatrique — {poids:.0f} kg</div>')
            _det_ped = SS.det if isinstance(SS.det, dict) else {}
            _dur_epi  = float(_det_ped.get("duree_min", 0) or 0)
            _encours  = bool(_det_ped.get("en_cours", False))
            _dur_epi_i = st.number_input("Durée de crise (min)", 0.0, 120.0, _dur_epi, 0.5, key="ph_dur_epi")
            _encours_i = st.checkbox("Crise en cours", value=_encours, key="ph_encours_epi")
            _eme = protocole_epilepsie_ped(poids, age, _dur_epi_i, _encours_i, atcd) or {}
            if _eme.get("eme_etabli"):
                AL(f"EME établi ({_dur_epi_i:.0f} min) — 2e ligne", "danger")
            if _encours_i:
                AL("Crise EN COURS — anticonvulsivant IMMÉDIAT", "danger")

            _e1, _e2 = st.columns(2)
            for _col, _drug_key, _name in [
                (_e1, "midazolam_buccal", "Midazolam buccal"),
                (_e2, "diazepam_rectal",  "Diazépam rectal"),
                (_e1, "lorazepam_iv",     "Lorazépam IV"),
                (_e2, "levetiracetam_iv", "Lévétiracétam IV"),
            ]:
                _d = _eme.get(_drug_key) or {}
                if _d.get("dose"):
                    with _col:
                        H(f'<div class="rx-compact"><div class="rx-compact-dose" style="font-size:.85rem;">{_d["dose"]}</div>'
                          f'<div class="rx-compact-info"><div class="rx-compact-name">{_name}</div>'
                          f'<div class="rx-compact-detail">{_d.get("note","")}</div></div></div>')

            st.divider()
            H('<div class="card-title">Kétamine intranasale</div>')
            _ki, _kie = ketamine_intranasale(poids, age, atcd)
            if _kie: AL(_kie, "warning")
            else:
                H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_ki or {}).get("dose_mg",0):.0f} mg IN</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Kétamine intranasale</div>'
                  f'<div class="rx-compact-detail">{(_ki or {}).get("admin","")} — Onset {(_ki or {}).get("onset","")}</div></div></div>')

            st.divider()
            H('<div class="card-title">Midazolam IM / IN (Hypnovel® 5 mg/ml)</div>')
            _mi_im, _mi_im_err = midazolam_im(poids, age, atcd)
            if _mi_im_err: AL(_mi_im_err, "danger")
            else:
                for _ma, _mc in (_mi_im or {}).get("alerts", []): AL(_ma, _mc)
                H(f'<div class="rx-compact"><div class="rx-compact-dose">{(_mi_im or {}).get("dose_mg",0):.1f} mg ({(_mi_im or {}).get("volume_ml",0):.2f} ml)</div>'
                  f'<div class="rx-compact-info"><div class="rx-compact-name">Midazolam IM/IN (Hypnovel® 5 mg/ml)</div>'
                  f'<div class="rx-compact-detail">{(_mi_im or {}).get("admin","")}</div>'
                  f'<div class="rx-compact-detail" style="color:#64748B;">Onset : {(_mi_im or {}).get("onset","")}</div></div></div>')

    # ── Générateur d'étiquette PSE (hors sous-onglets) ────────────────────────
    st.divider()
    with st.expander("🏷️ Générateur d'étiquette PSE — traçabilité seringue", expanded=False):
        st.caption("Compatible AR 78 AFMPS 2019 — Identification seringue auto-pousseuse")
        _eq1, _eq2, _eq3 = st.columns(3)
        _eq_med   = _eq1.text_input("Médicament", value="Morphine",   key=WK("eq_med"))
        _eq_conc  = _eq2.number_input("Concentration (mg/ml)", 0.01, 50.0, 1.0, 0.1, key="eq_conc")
        _eq_vol   = _eq3.number_input("Volume total (ml)", 10, 100, 50, key="eq_vol")
        _eq4, _eq5 = st.columns(2)
        _eq_debit = _eq4.number_input("Débit PSE (ml/h)", 0.1, 100.0, 5.0, 0.5, key="eq_debit")
        _eq_op    = _eq5.text_input("Opérateur", value=SS.op or "IAO", key="eq_op")
        if _eq_debit and _eq_conc:
            _eq_txt = generer_etiquette(
                medicament=_eq_med, concentration=_eq_conc,
                debit_mlh=_eq_debit, vol_total=_eq_vol,
                poids=poids, operateur=_eq_op or "IAO",
            )
            st.code(_eq_txt, language=None)
            st.download_button("🖨️ Télécharger (.txt)", data=_eq_txt,
                file_name=f"etiq_{_eq_med}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain", use_container_width=True)

    # ── _PH[5] — CALCUL DE PERFUSIONS IV ─────────────────────────────────────
    with _PH[5]:
        H(f'''<div style="background:linear-gradient(135deg,#0F172A,#1E3A5F);color:#fff;
            border-radius:10px;padding:12px 16px;margin-bottom:12px;">
          <div style="font-size:.72rem;opacity:.75;text-transform:uppercase;letter-spacing:.1em;">Calcul perfusion</div>
          <div style="font-size:1.05rem;font-weight:800;">Patient : {poids:.0f} kg</div>
          <div style="font-size:.72rem;opacity:.75;margin-top:2px;">Concentrations standard Hainaut — BCFI Belgique</div>
        </div>''')

        H('<div class="card-title">⏱ Timers médicaments</div>')
        st.caption("Horodatage des administrations — Alertes automatiques")
        _tm_c1, _tm_c2 = st.columns([3,1])
        _tm_nom = _tm_c1.text_input("Médicament / Action", placeholder="ex: Ceftriaxone IV, Naloxone, Paracétamol…", key=WK("tm_nom"))
        if _tm_c2.button("▶ Démarrer", key=WK("tm_start"), use_container_width=True):
            if _tm_nom.strip():
                SS["timers"] = SS.get("timers") or {}
                SS["timers"][_tm_nom.strip()] = datetime.now()
        if SS.get("timers"):
            for _tn, _ts in list(SS["timers"].items()):
                _elapsed = (datetime.now() - _ts).total_seconds()
                _em, _es = divmod(int(_elapsed), 60)
                _eh, _em2 = divmod(_em, 60)
                _timer_str = f"{_eh:02d}:{_em2:02d}:{_es:02d}" if _eh else f"{_em:02d}:{_es:02d}"
                _tc = "#EF4444" if _elapsed > 3600 else "#F59E0B" if _elapsed > 1800 else "#22C55E"
                _ta, _tb = st.columns([5, 1])
                H(f'<div style="background:#0F172A;border-left:4px solid {_tc};border-radius:0 6px 6px 0;'
                  f'padding:6px 12px;margin:3px 0;display:flex;justify-content:space-between;align-items:center;">'
                  f'<span style="font-size:.78rem;color:#E2E8F0;">{_tn}</span>'
                  f'<span style="font-family:monospace;font-weight:700;color:{_tc};">{_timer_str}</span></div>')
                if _ta.button(f"🗑 {_tn[:15]}", key=WK(f"tm_del_{_tn[:12]}"), use_container_width=True):
                    del SS["timers"][_tn]; st.rerun()
        st.divider()

        with st.expander("📊 Dilutions standard Hainaut + Calculateur Noradrénaline", expanded=True):
            section_dilutions_hainaut()
            st.divider()
            calculateur_noradrenaline(poids_defaut=float(poids))

        st.markdown("**Choisir la perfusion à calculer :**")
        _perf_choice = st.selectbox("Médicament / Indication", [
            "— Sélectionner —",
            "Morphine PSE — Analgésie IV continue",
            "Dipidolor® PSE — Analgésie IV continue",
            "Kétamine PSE — Analgésie subanesthésique",
            "Midazolam PSE — Sédation / Convulsion",
            "Adrénaline IV — Anaphylaxie / Choc",
            "Noradrénaline IV — Choc septique (SSC 2021)",
            "Dobutamine IV — Choc cardiogénique",
            "Amiodarone IV — FA / TV stable",
            "Labétalol IV — HTA sévère / Dissection",
            "Nicardipine IV — HTA sévère (alternative)",
            "Magnésium IV — Pré-éclampsie / Torsades",
            "Insuline rapide IV — Acidocétose / Hyperglycémie",
            "🔢 Convertisseur débit ↔ dose",
        ], key="perf_choice")

        H("""<style>
        @keyframes compatFlash {
          0%, 100% { background:#7F1D1D; box-shadow:0 0 0 rgba(239,68,68,0); }
          50% { background:#DC2626; box-shadow:0 0 0 6px rgba(239,68,68,.24); }
        }
        .compat-red-flash {
          animation: compatFlash .9s ease-in-out infinite;
          border:2px solid #FCA5A5;
          border-radius:10px;
          color:#FEE2E2;
          font-weight:900;
          margin:8px 0 12px;
          padding:14px 16px;
          text-align:center;
        }
        </style>""")
        _current_iv_med = med_from_perfusion_choice(_perf_choice)
        if _current_iv_med:
            _y_partner = st.selectbox(
                "Compatibilité Y — médicament déjà branché",
                ["— aucun —"] + get_substances_list(),
                key=WK("perf_y_partner"),
                help="Contrôle rapide HUG par paire. En cas de doute: pharmacie clinique.",
            )
            if _y_partner != "— aucun —":
                _compat = check_iv_compatibility(_current_iv_med, _y_partner)
                if _compat["statut"] == "Incompatible":
                    H(
                        f'<div class="compat-red-flash">⚠️ ALERTE COMPATIBILITÉ : '
                        f'{_compat["med_a"]} + {_compat["med_b"]} = Risque de précipitation.</div>'
                    )
                    if _compat.get("precision"):
                        AL(_compat["precision"], "danger")
                elif _compat["statut"] == "Prudence":
                    AL(f"Compatibilité Y à vérifier : {_compat['message']}", "warning")
                    if _compat.get("precision"):
                        st.caption(_compat["precision"])
                else:
                    AL(f"Compatibilité Y OK : {_compat['message']}", "success")

        def _rx_perf(p: dict) -> None:
            if not p:
                return
            _details_html = ""
            if p.get("details"):
                _items = "".join(f'<div style="font-size:.72rem;color:#94A3B8;margin:2px 0;">• {d}</div>' for d in p["details"])
                _details_html = f'<div style="border-top:1px solid #1E293B;margin-top:10px;padding-top:8px;">{_items}</div>'
            H(f'''<div style="background:#0F172A;border:1.5px solid #334155;border-radius:10px;padding:14px 18px;margin:10px 0;">
              <div style="font-size:.72rem;color:#64748B;text-transform:uppercase;letter-spacing:.1em;">{p.get("label","")}</div>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px;">
                <div style="text-align:center;">
                  <div style="font-size:2rem;font-weight:900;color:#38BDF8;font-family:\'IBM Plex Mono\',monospace;">{p.get("debit_mlh",0)}</div>
                  <div style="font-size:.72rem;color:#64748B;">ml/h</div></div>
                <div style="text-align:center;">
                  <div style="font-size:2rem;font-weight:900;color:#A78BFA;font-family:\'IBM Plex Mono\',monospace;">{int(p.get("gttes_min",0))}</div>
                  <div style="font-size:.72rem;color:#64748B;">gttes/min</div></div>
                <div style="text-align:center;">
                  <div style="font-size:1.3rem;font-weight:900;color:#4ADE80;font-family:\'IBM Plex Mono\',monospace;">{p.get("conc_mgml",0)}</div>
                  <div style="font-size:.72rem;color:#64748B;">mg/ml</div></div>
              </div>
              <div style="border-top:1px solid #1E293B;margin-top:12px;padding-top:10px;">
                <div style="font-size:.7rem;color:#94A3B8;margin-bottom:6px;font-weight:600;">DILUTION :</div>
                <div style="font-size:.75rem;color:#CBD5E1;">{p.get("dilution","")}</div>
              </div>
              {_details_html}
              <div style="font-size:.72rem;color:#475569;margin-top:8px;font-style:italic;">{p.get("ref","")}</div>
            </div>''')
            for _am, _ac in p.get("alerts", []):
                AL(_am, _ac)
            if p.get('duree_h', 0) > 0:
                st.caption(f"Durée d'autonomie : ≈ {p['duree_h']:.1f} h ({p['vol_total_ml']:.0f} ml à {p['debit_mlh']:.1f} ml/h)")

        if _perf_choice == "Morphine PSE — Analgésie IV continue":
            _pc1, _pc2 = st.columns(2)
            _mo_dose = _pc1.number_input("Dose µg/kg/h", 5.0, 80.0, 20.0, 5.0, key="pm_dose")
            _mo_vol  = _pc2.selectbox("Volume seringue (ml)", [20, 50], index=1, key="pm_vol")
            _rx_perf(perf_morphine(poids, _mo_dose, _mo_vol, atcd))

        elif _perf_choice == "Dipidolor® PSE — Analgésie IV continue":
            _pc1, _pc2 = st.columns(2)
            _pi_dose = _pc1.number_input("Dose µg/kg/h", 5.0, 60.0, 15.0, 5.0, key="pp_dose")
            _pi_vol  = _pc2.selectbox("Volume seringue (ml)", [20, 50], index=1, key="pp_vol")
            _rx_perf(perf_piritramide(poids, _pi_dose, _pi_vol, atcd))

        elif _perf_choice == "Kétamine PSE — Analgésie subanesthésique":
            _ke_ind = st.radio("Indication", ["analgesie","sedation"],
                format_func=lambda x: {"analgesie":"Analgésie (0,1-0,5 mg/kg/h)", "sedation":"Sédation légère (0,5-2 mg/kg/h)"}[x],
                horizontal=True, key="pke_ind")
            _rx_perf(perf_ketamine(poids, _ke_ind, atcd))

        elif _perf_choice == "Midazolam PSE — Sédation / Convulsion":
            _mi_ind = st.radio("Indication", ["sedation","convulsion","anxiolyse"],
                format_func=lambda x: {"sedation":"Sédation","convulsion":"Convulsion","anxiolyse":"Anxiolyse"}[x],
                horizontal=True, key="pmi_ind")
            _rx_perf(perf_midazolam(poids, _mi_ind, atcd))

        elif _perf_choice == "Adrénaline IV — Anaphylaxie / Choc":
            _ae_ind = st.radio("Indication", ["anaphylaxie","choc_septique"],
                format_func=lambda x: {"anaphylaxie":"Anaphylaxie sévère","choc_septique":"Choc vasoplégique"}[x],
                horizontal=True, key="pae_ind")
            _rx_perf(perf_adrenaline(poids, _ae_ind, atcd))

        elif _perf_choice == "Noradrénaline IV — Choc septique (SSC 2021)":
            _na_dose = st.number_input("Dose initiale µg/kg/min", 0.05, 3.0, 0.1, 0.05, key="pna_dose")
            _rx_perf(perf_noradrenaline(poids, _na_dose, atcd))

        elif _perf_choice == "Dobutamine IV — Choc cardiogénique":
            _db_dose = st.number_input("Dose µg/kg/min", 2.0, 20.0, 5.0, 2.5, key="pdb_dose")
            _rx_perf(perf_dobutamine(poids, _db_dose, atcd))

        elif _perf_choice == "Amiodarone IV — FA / TV stable":
            _am_ind = st.radio("Indication", ["fa","tv_stable","choc_refractaire"],
                format_func=lambda x: {"fa":"FA récente","tv_stable":"TV hémostable","choc_refractaire":"ACR / FV réfractaire"}[x],
                horizontal=True, key="pam_ind")
            _rx_perf(perf_amiodarone(poids, _am_ind, atcd))

        elif _perf_choice == "Labétalol IV — HTA sévère / Dissection":
            _lb_ctx = st.selectbox("Contexte", ["hta_severe","dissection_aortique"], key="plb_ctx",
                format_func=lambda x: {"hta_severe":"HTA sévère","dissection_aortique":"Dissection aortique (cible < 120)"}[x])
            _rx_perf(perf_labetalol(poids, _lb_ctx, atcd))

        elif _perf_choice == "Nicardipine IV — HTA sévère (alternative)":
            _rx_perf(perf_nicardipine(poids, atcd))

        elif _perf_choice == "Magnésium IV — Pré-éclampsie / Torsades":
            _mg_ind = st.radio("Indication", ["eclampsia","torsades","asthme"],
                format_func=lambda x: {"eclampsia":"Pré-éclampsie","torsades":"Torsades de pointes","asthme":"Asthme sévère réfractaire"}[x],
                horizontal=True, key="pmg_ind")
            _rx_perf(perf_magnesium(poids, _mg_ind, atcd))

        elif _perf_choice == "Insuline rapide IV — Acidocétose / Hyperglycémie":
            _in_ind = st.radio("Indication", ["acidocetose","hyperkaliemie","hyperglycemie"],
                format_func=lambda x: {"acidocetose":"Acidocétose","hyperkaliemie":"Hyperkaliémie","hyperglycemie":"Hyperglycémie"}[x],
                horizontal=True, key="pin_ind")
            _in_gl = float(SS.gl or 300)
            _rx_perf(perf_insuline(poids, _in_ind, _in_gl, atcd))

        elif _perf_choice == "🔢 Convertisseur débit ↔ dose":
            st.markdown("##### Convertisseur universel ml/h ↔ dose")
            _cv_c1, _cv_c2 = st.columns(2)
            _cv_conc  = _cv_c1.number_input("Concentration (mg/ml)", 0.001, 50.0, 1.0, 0.1, key="cv_conc")
            _cv_poids = float(poids)
            _cv_c2.metric("Poids patient", f"{_cv_poids:.0f} kg")
            _cv_c2.caption("Synchronisé depuis l'onglet Patient.")

            st.markdown("**→ Débit → Dose :**")
            _cv_debit = st.number_input("Débit connu (ml/h)", 0.1, 500.0, 10.0, 0.5, key="cv_debit")
            _cv_res = convertir_debit(_cv_debit, _cv_conc, _cv_poids)
            H(f'''<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:12px;margin:6px 0;">
              <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;">
                <div><div style="font-size:.72rem;color:#64748B;">Dose mg/h</div>
                  <div style="font-size:1.1rem;font-weight:700;color:#004A99;">{_cv_res["dose_mg_h"]:.3f} mg/h</div></div>
                <div><div style="font-size:.72rem;color:#64748B;">mg/kg/h</div>
                  <div style="font-size:1.1rem;font-weight:700;color:#004A99;">{_cv_res["dose_mg_kg_h"]:.4f} mg/kg/h</div></div>
                <div><div style="font-size:.72rem;color:#64748B;">µg/kg/min</div>
                  <div style="font-size:1.1rem;font-weight:700;color:#7C3AED;">{_cv_res["dose_ug_kg_min"]:.3f} µg/kg/min</div></div>
                <div><div style="font-size:.72rem;color:#64748B;">Gttes/min (20 gttes/ml)</div>
                  <div style="font-size:1.1rem;font-weight:700;color:#16A34A;">{int(_cv_debit*20/60)} gttes/min</div></div>
              </div>
            </div>''')

            st.markdown("**→ Dose → Débit :**")
            _cv_dose2 = st.number_input("Dose souhaitée (mg/h)", 0.001, 1000.0, 1.0, 0.1, key="cv_dose2")
            _cv_calc  = calculer_debit(_cv_dose2, _cv_conc)
            H(f'''<div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;padding:12px;margin:6px 0;">
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
                <div><div style="font-size:.72rem;color:#166534;">Débit ml/h</div>
                  <div style="font-size:1.3rem;font-weight:800;color:#166534;">{_cv_calc["debit_mlh"]:.1f} ml/h</div></div>
                <div><div style="font-size:.72rem;color:#166534;">Gttes/min adulte (×20)</div>
                  <div style="font-size:1.3rem;font-weight:800;color:#166534;">{int(_cv_calc["gttes_min_adulte"])} gttes/min</div></div>
                <div><div style="font-size:.72rem;color:#166534;">Microgottes/min (×60)</div>
                  <div style="font-size:1.3rem;font-weight:800;color:#166534;">{int(_cv_calc["gttes_min_ped"])} µgttes/min</div></div>
              </div>
            </div>''')

        _render_rea_database(WK)
        section_fiches_medicaments()
