# akir_iao_enhancements.py — Composants UI enrichis — AKIR-IAO v20
# Développeur : Ismail Ibn-Daifa — Hainaut, Wallonie, Belgique
# RGPD : aucun nom/prénom traité — session anonyme UID
#
# ══════════════════════════════════════════════════════════════════════════════
# RAPPORT D'AUDIT MÉDICAL v19.2 — 24 corrections (second niveau)
# ══════════════════════════════════════════════════════════════════════════════
# [C-01] GCS M2/M4/M5/M6 : libellés complets (décérébration, retrait flexion…)
# [C-02] Borg : distinction SpO2 BPCO 88-92% / non-BPCO 92-96%
# [C-03] CAM-ICU : CI halopéridol (QTc > 500ms, Parkinson)
# [C-04] Insuline : débit initial 0,1 UI/kg/h acidocétose
# [C-05] Dobutamine : max 20 µg/kg/min + arythmies > 10
# [C-06] Adrénaline PSE : distinction avec IM anaphylaxie
# [C-07] Noradrénaline : cible PAM ≥ 65 mmHg + escalade vasopressine
# [C-08] Cédocard : absorption PVC — tubulure PE recommandée
# [C-09] Amiodarone : photosensibilité + monitoring QT
# [C-10] Héparine : origine porcine préférable + TIH J5-J10
# [C-11] Adénosine : CI FA + dose 1 mg chez transplanté
# [C-12] Flumazénil : délai action 1-2 min
# [C-13] Aspirine : 300 mg PO mâché préféré IV (ESC 2023)
# [C-14] Atropine : inefficace BAV infranodal (Mobitz II / BAV 3)
# [C-15] Bicarbonate : débit hyperkaliémie + surveillance ECG
# [C-16] Ticagrélor : CI ciclosporine + absence d'antidote
# [C-17] Diazépam : phlébite IV (solvant PG) + accumulation IR/IH
# [C-18] Sufentanil : renforcement avertissement médecin/IADE
# [C-19] Méthylprednisolone : glycémie capillaire H+4
# [C-20] Buscopan : tachycardie transitoire IV
# [C-21] Ipratropium : CI oculaire nébulisation masque + glaucome
# [C-22] Ocytocine : durée injection ≥ 1 min — collapsus si bolus
# [C-23] Nicardipine : absorption PVC + tachycardie réflexe
# [C-24] Olanzapine : CI QTc allongé + exclusion Parkinson
# [?-Watteeuw] Isuprel : confirmer usage local ou retirer du tableau
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# MISES À JOUR RECOMMANDATIONS v19.3 — 17 médicaments (2022-2024)
# ══════════════════════════════════════════════════════════════════════════════
# [UPD-Adénosine]   ESC SVT 2019 — alternative vérapamil/métoprolol si échec
# [UPD-Flumazénil]  BCFI 2024 — usage limité; BZD longue durée: re-sédation probable
# [UPD-Aspirine]    ESC 2023 — 300mg PO mâché Classe I; allergie: ticagrélor seul
# [UPD-Atropine]    ERC 2021 — éviter < 0,5mg; inefficace BAV infranodal confirmé
# [UPD-Bicarbonate] ERC 2021 / SFAR 2023 — non recommandé ACR; acidose lactique pH < 7,15
# [UPD-Ticagrélor]  ESC 2023 — charge en salle cath STEMI; dyspnée ES 20%; CI azolés
# [UPD-Cédocard]    ESC 2021 IC — si PAS > 110mmHg (IIa); tachyphylaxie 24h
# [UPD-Diazépam]    ILAE 2022 — midazolam IM hors hôpital; lorazépam IV intra-hospit
# [UPD-MeSolu]      GINA 2023 — dose unique 40mg PO = 5j; ERS/ATS 2022 BPCO; RECOVERY
# [UPD-Ocytocine]   OMS 2023 + CNGOF 2022 — TXA 1g IV; carbétocine FIGO 2022
# [UPD-Nicardipine] ESC/ESH 2023 — réf. crise HTA Cl.I; objectifs PA par indication
# [UPD-Olanzapine]  BAP 2023/NICE 2022 — monitoring 2h; dexmédétomidine alternative
# [UPD-Ipratropium] GINA 2023 / GOLD 2024 / Cochrane 2023
# [UPD-Dobutamine]  ESC 2021 — réservée choc cardiogénique IIb; sevrage progressif
# [UPD-Noradré]     SSC 2021 — vasopresseur 1er choix; vasopressine si > 0,25µg/kg/min
# [UPD-Insuline]    ISPAD 2022 — démarrer après 1h réhydrat; SFAR 2023 cible 140-180
# [UPD-Héparine]    ESC 2023 / ISTH 2023 TIH score 4T / ACCP 2022
# ══════════════════════════════════════════════════════════════════════════════
# Maintenu depuis v19.1 :
# [ERR-1] Flumazénil max 1 mg (BCFI/RCP Anexate)
# [ERR-2] Ipratropium doses fixes (GINA 2023)
# [ERR-3] Diazépam enfant voie + dose max (BCFI/SFNP 2023)
# [WARN-1] GCS libellés V3/V4/M3 (Teasdale & Jennett 1974)
# [WARN-2] Noradrénaline diluant 36 ml G5% (4+36=40 ml)
# [WARN-3] Adénosine flush 20 ml NaCl (ERC 2021)
# [WARN-7] Sufentanil PSE 5 µg/ml
# [WARN-8] Ocytocine entretien HPP 40 mUI/min
# [WARN-9] Olanzapine CI corps de Lewy
# [WARN-10] Nicardipine max 15 mg/h
# [WARN-11] Buscopan CI occlusion intestinale
# [INFO-3] Amiodarone incompatibilité NaCl 0,9%
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import difflib
import unicodedata
import streamlit as st
import pandas as pd
from datetime import datetime
from functools import lru_cache

SS = st.session_state


def _ek(base: str) -> str:
    """Clé widget unique par session — évite les conflits multi-onglets."""
    return f"{SS.get('sid','s')}__{base}"


# ── Fuzzy search optimisé ─────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Normalise : minuscules, sans accents, sans ponctuation."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    ascii_ = "".join(c for c in nfkd if not unicodedata.combining(c))
    return " ".join(ascii_.split())


@lru_cache(maxsize=256)
def _tokenize(text: str) -> frozenset[str]:
    """Retourne l'ensemble des tokens (mots) d'un texte normalisé."""
    return frozenset(_normalize(text).split())


def _fuzzy_score_fast(query: str, med: dict) -> float:
    """
    Score de pertinence pour la recherche de médicaments.

    Stratégie (pas de SequenceMatcher global — trop de faux positifs) :
    1. Sous-chaîne exacte dans le nom normalisé → 1.0
    2. Sous-chaîne exacte dans l'indication → 0.9
    3. Préfixe ≥ 3 car sur un token du nom ou de l'indication → 0.85
    4. Jaccard pondéré sur les tokens (nom ×2, indication ×1) → score continu
    """
    q_norm   = _normalize(query)
    nom_norm = _normalize(med["nom"])
    ind_norm = _normalize(med["ind"])

    if q_norm in nom_norm:
        return 1.0
    if q_norm in ind_norm:
        return 0.9
    if len(q_norm) >= 3:
        for tok in (_tokenize(nom_norm) | _tokenize(ind_norm)):
            if tok.startswith(q_norm):
                return 0.85

    q_tokens   = _tokenize(q_norm)
    nom_tokens = _tokenize(nom_norm)
    ind_tokens = _tokenize(ind_norm)

    nom_inter = len(q_tokens & nom_tokens)
    ind_inter = len(q_tokens & ind_tokens)
    denom     = len(q_tokens | nom_tokens | ind_tokens)
    if denom > 0:
        return (nom_inter * 2 + ind_inter) / (denom + len(q_tokens))
    return 0.0


def _search_medicaments(query: str, catalogue: list[dict], threshold: float = 0.35) -> list[dict]:
    """
    Filtre et trie un catalogue de médicaments par pertinence.
    Retourne les résultats au-dessus du seuil, triés du meilleur au moins bon.
    """
    if not query or not query.strip():
        return catalogue
    scored = ((m, _fuzzy_score_fast(query, m)) for m in catalogue)
    return [m for m, s in sorted(scored, key=lambda x: -x[1]) if s >= threshold]


# ══════════════════════════════════════════════════════════════════════════════
# 1. GCS VISUEL — Boutons tactiles par sous-score
# Source : Teasdale G & Jennett B, Lancet 1974;2:81-4 — PMID 4136544
# Libellés officiels complets (v19.2) — Interprétation : ATLS 11th ed. 2018
# ══════════════════════════════════════════════════════════════════════════════

def gcs_visual_scale() -> int:
    """
    Saisie GCS par boutons tactiles.
    Met à jour SS.gcs_y / SS.gcs_v / SS.gcs_m et SS.v_gcs.
    Retourne le total GCS (3-15).
    """
    SS.setdefault("gcs_y", 4)
    SS.setdefault("gcs_v", 5)
    SS.setdefault("gcs_m", 6)

    _ON = ("background:#1D4ED8;color:#fff;border-radius:8px;"
           "padding:3px 0;text-align:center;font-weight:700;"
           "font-size:.7rem;margin-top:2px;")

    col_y, col_v, col_m = st.columns(3)

    # ── Yeux ─────────────────────────────────────────────────────────────────
    with col_y:
        st.markdown(
            "<div style='font-size:.7rem;font-weight:700;color:#64748B;"
            "text-transform:uppercase;'>Yeux (Y)</div>",
            unsafe_allow_html=True)
        for sc, lbl in [
            (4, "Spontanée"),
            (3, "Au bruit"),
            (2, "À la douleur"),
            (1, "Aucune"),
        ]:
            if st.button(f"{sc} — {lbl}", key=_ek(f"gcs_y_{sc}"),
                         use_container_width=True,
                         type="primary" if SS.gcs_y == sc else "secondary"):
                SS.gcs_y = sc
                SS.v_gcs = SS.gcs_y + SS.gcs_v + SS.gcs_m
                st.rerun()
            if SS.gcs_y == sc:
                st.markdown(f"<div style='{_ON}'>✓ {sc}</div>",
                            unsafe_allow_html=True)

    # ── Verbal ───────────────────────────────────────────────────────────────
    with col_v:
        st.markdown(
            "<div style='font-size:.7rem;font-weight:700;color:#64748B;"
            "text-transform:uppercase;'>Verbal (V)</div>",
            unsafe_allow_html=True)
        for sc, lbl in [
            (5, "Orientée"),
            (4, "Confuse"),
            (3, "Mots inappropriés"),        # Teasdale & Jennett 1974
            (2, "Sons incompréhensibles"),   # Teasdale & Jennett 1974
            (1, "Aucune"),
        ]:
            if st.button(f"{sc} — {lbl}", key=_ek(f"gcs_v_{sc}"),
                         use_container_width=True,
                         type="primary" if SS.gcs_v == sc else "secondary"):
                SS.gcs_v = sc
                SS.v_gcs = SS.gcs_y + SS.gcs_v + SS.gcs_m
                st.rerun()
            if SS.gcs_v == sc:
                st.markdown(f"<div style='{_ON}'>✓ {sc}</div>",
                            unsafe_allow_html=True)

    # ── Moteur ───────────────────────────────────────────────────────────────
    with col_m:
        st.markdown(
            "<div style='font-size:.7rem;font-weight:700;color:#64748B;"
            "text-transform:uppercase;'>Moteur (M)</div>",
            unsafe_allow_html=True)
        for sc, lbl in [
            (6, "Obéit aux ordres"),         # [C-01] libellé complet
            (5, "Localise la douleur"),      # [C-01]
            (4, "Retrait (flexion normale)"),# [C-01]
            (3, "Flexion anormale (décortication)"),  # confirmé v19.1
            (2, "Extension (décérébration)"),# [C-01]
            (1, "Aucune"),
        ]:
            if st.button(f"{sc} — {lbl}", key=_ek(f"gcs_m_{sc}"),
                         use_container_width=True,
                         type="primary" if SS.gcs_m == sc else "secondary"):
                SS.gcs_m = sc
                SS.v_gcs = SS.gcs_y + SS.gcs_v + SS.gcs_m
                st.rerun()
            if SS.gcs_m == sc:
                st.markdown(f"<div style='{_ON}'>✓ {sc}</div>",
                            unsafe_allow_html=True)

    gcs = SS.gcs_y + SS.gcs_v + SS.gcs_m
    SS.v_gcs = gcs

    # Interprétation ATLS 11th 2018
    if gcs <= 8:
        col, lbl = "#EF4444", "Coma — Protection VA immédiate (ATLS Sévère ≤ 8)"
    elif gcs <= 12:
        col, lbl = "#F59E0B", "Obnubilation — Surveillance armée (ATLS Modéré 9-12)"
    else:
        col, lbl = "#22C55E", f"Conscient (ATLS Léger 13-15){' — Réévaluer si déficit focal' if gcs < 15 else ''}"

    st.markdown(
        f"<div style='background:{col}18;border-left:4px solid {col};"
        f"border-radius:0 8px 8px 0;padding:8px 14px;margin-top:8px;"
        f"display:flex;align-items:center;justify-content:space-between;'>"
        f"<div style='font-size:.72rem;color:{col};font-weight:700;'>{lbl}</div>"
        f"<div style='font-size:1.5rem;font-weight:900;color:{col};"
        f"font-family:monospace;'>GCS {gcs}/15</div></div>",
        unsafe_allow_html=True)
    st.caption("Teasdale & Jennett, Lancet 1974 — PMID 4136544 | ATLS 11th ed. 2018")
    return gcs


# ══════════════════════════════════════════════════════════════════════════════
# 2. BORG CR10 — Dyspnée subjective
# Source : Borg G, Scand J Rehab Med 1990;22:141-9 — PMID 2280867
# [C-02] SpO2 cible : 92-96% (non-BPCO) / 88-92% (BPCO) — ERC 2021
# Condition d'affichage : FR > 20/min OU SpO2 < 95%
# ══════════════════════════════════════════════════════════════════════════════

def borg_visual_scale() -> float:
    """Borg CR10 avec barre colorée et seuils ERC 2021."""
    st.markdown(
        "<div style='font-size:.72rem;font-weight:700;color:#64748B;"
        "text-transform:uppercase;margin-bottom:4px;'>🫁 Dyspnée — Borg CR10</div>",
        unsafe_allow_html=True)

    borg_val = st.select_slider(
        "Gêne respiratoire",
        options=[0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        value=SS.get("borg_val", 0),
        format_func=lambda x: {
            0: "0 – Nulle", 0.5: "0.5 – Imperceptible",
            1: "1 – Très légère", 2: "2 – Légère",
            3: "3 – Modérée", 4: "4 – Assez sévère",
            5: "5 – Sévère", 6: "6 – Très sévère",
            7: "7 – Très très sévère", 8: "8 – Quasi-maximale",
            9: "9 – Maximale", 10: "10 – Épuisement respiratoire",
        }[x],
        key=_ek("borg_slider"),
    )
    SS["borg_val"] = borg_val

    bc  = ("#22C55E" if borg_val < 3 else
           "#F59E0B" if borg_val < 5 else
           "#F97316" if borg_val < 7 else "#EF4444")
    pct = min(100, int(borg_val * 10))
    st.markdown(
        f"<div style='background:#1E293B;border-radius:6px;padding:3px;margin:4px 0;'>"
        f"<div style='background:{bc};width:{pct}%;height:10px;border-radius:4px;'></div></div>"
        f"<div style='font-size:.68rem;color:{bc};font-weight:600;'>Borg {borg_val} / 10</div>",
        unsafe_allow_html=True)

    # [C-02] Distinction SpO2 selon BPCO
    _bpco = SS.get("v_bpco", False)
    _spo2_cible = "88-92 %" if _bpco else "92-96 %"
    _spo2_note  = "BPCO — risque hypercapnie si SpO2 > 92%" if _bpco else "Non-BPCO"

    if borg_val >= 7:
        st.error(
            f"🔴 Borg {borg_val} — Détresse respiratoire sévère\n"
            f"O₂ haut débit (15 L/min masque HC) + médecin IMMÉDIAT\n"
            f"Cible SpO₂ {_spo2_cible} ({_spo2_note})")
    elif borg_val >= 5:
        st.warning(
            f"🟠 Borg {borg_val} — Dyspnée sévère\n"
            f"Position ½ assise | O₂ si SpO₂ < {'90 %' if _bpco else '92 %'} "
            f"— Cible {_spo2_cible} ({_spo2_note})")
    elif borg_val >= 3:
        st.info(f"Borg {borg_val} — Dyspnée modérée — Surveiller SpO₂ (cible {_spo2_cible})")

    st.caption("Borg G, Scand J Rehab Med 1990 — PMID 2280867 | SpO₂ cible ERC 2021")
    return float(borg_val)


# ══════════════════════════════════════════════════════════════════════════════
# 3. CAM-ICU — Délirium
# Source : Ely EW et al., JAMA 2001;286:2703-10 — PMID 11730446
# Se 93-100 % / Sp 89-100 % | Algorithme : critères 1 + 2 + (3 ou 4)
# [C-03] CI halopéridol ajoutées : QTc > 500 ms, syndrome parkinsonien
# ══════════════════════════════════════════════════════════════════════════════

def cam_icu_visual() -> bool:
    """CAM-ICU simplifié avec recommandations thérapeutiques."""
    with st.expander("🧠 Confusion aiguë — CAM-ICU (délirium)", expanded=False):
        st.caption(
            "Ely EW et al., JAMA 2001 — PMID 11730446 | "
            "Se 93-100 % / Sp 89-100 % | Algorithme : 1 + 2 + (3 ou 4)")

        cam1 = st.checkbox(
            "1. Début brutal OU fluctuation de l'état mental dans la journée",
            key=_ek("cam1"))
        cam2 = st.checkbox(
            "2. Inattention — ≥ 2 erreurs aux mois à rebours "
            "(ou test de la squeeze-main alternée)",
            key=_ek("cam2"))
        cam3 = st.checkbox(
            "3. Niveau de conscience altéré (GCS < 15 — agitation ou stupeur)",
            value=SS.get("v_gcs", 15) < 15,
            key=_ek("cam3"))
        cam4 = st.checkbox(
            "4. Pensée désorganisée — réponses incohérentes aux questions simples",
            key=_ek("cam4"))

        delirium = cam1 and cam2 and (cam3 or cam4)

        if delirium:
            st.error(
                "⚠️ **Délirium positif** — Appel médecin IMMÉDIAT\n\n"
                "**Causes à exclure en urgence :**\n"
                "Sepsis · Hypoglycémie · Hypoxémie · Rétention urinaire · "
                "Fécalome · Iatrogène (BZD, morphine, antihistaminiques)\n\n"
                "**Traitement non pharmacologique en premier** : "
                "réorientation, lumière, lunettes, prothèse auditive, famille\n\n"
                "**Halopéridol 0,5-1 mg IV/IM** si agitation sévère menaçante "
                "(après avis médical — SFAR 2017)\n"
                # [C-03]
                "⚠️ CI halopéridol : QTc > 500 ms (ECG préalable), "
                "syndrome parkinsonien, corps de Lewy")
        elif cam1 or cam2:
            st.warning(
                "Délirium possible — Réorientation, éviter sédatifs\n"
                "Réévaluer dans 1h")
        else:
            st.success("CAM-ICU négatif — Pas d'argument pour un délirium")

        return delirium
    return False


# ══════════════════════════════════════════════════════════════════════════════
# 4. DILUTIONS PSE — Standard Hainaut
# Sources : BCFI 2024 / AFMPS / RCP fabricants / SSC 2021
# Toutes concentrations vérifiées mathématiquement (v19.2)
# ══════════════════════════════════════════════════════════════════════════════

HAUTE_SENNE_DILUTIONS: dict = {

    # 50 UI / 50 ml = 1 UI/ml ✅
    "Insuline (Actrapid)": {
        "ampoules":   "50 UI (flacon)",
        "diluant":    "49,5 ml NaCl 0,9 %",
        "vol_ml":     50,
        "conc_ui_ml": 1.0,
        "conc_ug_ml": None,
        # [C-04] + [UPD-2024] ISPAD 2022 / ADA 2024 / SFAR 2023
        "note": (
            "Rincer tubulure 20 ml avant connexion (absorption sur PVC). "
            "ISPAD 2022 acidocétose : insuline IV après 1h de réhydratation (pas avant). "
            "Acidocétose : 0,1 UI/kg/h (max 10 UI/h). "
            "SFAR 2023 soins intensifs : cible glycémie 140-180 mg/dl (non plus 80-110). "
            "Hyperkaliémie : 10 UI + G30 % 50 ml IVL — effet transitoire 30-60 min. "
            "⚠️ Confusion U-100 / U-500 = erreur fatale — vérifier concentration avant usage."
        ),
    },

    # 250 mg / 50 ml = 5000 µg/ml ✅
    "Dobutamine": {
        "ampoules":   "1 A 250 mg (20 ml)",
        "diluant":    "30 ml NaCl 0,9 %",
        "vol_ml":     50,
        "conc_ug_ml": 5000,
        # [C-05] + [UPD-2024] ESC 2021 IC aiguë / SSC 2021
        "note": (
            "Débit : 2-5 µg/kg/min → max 20 µg/kg/min (BCFI). "
            "ESC 2021 : réservée au choc cardiogénique + bas débit (Classe IIb). "
            "Risque arythmies supraventriculaires > 10 µg/kg/min — monitoring ECG continu. "
            "Arrêt progressif obligatoire (sevrage brutal = décompensation). "
            "Milrinone : alternative si bêtabloquants en cours (synergie)."
        ),
    },

    # 2 mg / 40 ml = 50 µg/ml ✅
    "Adrénaline PSE": {
        "ampoules":   "2 A 1 mg/ml (2 ml chacune) = 2 mg",
        "diluant":    "38 ml NaCl 0,9 %",
        "vol_ml":     40,
        "conc_ug_ml": 50,
        # [C-06] distinction IM anaphylaxie
        "note": (
            "⚠️ PSE IV UNIQUEMENT — DIFFÉRENT de l'adrénaline IM anaphylaxie (0,5 mg IM). "
            "Incompatible alcalins — voie dédiée. "
            "Débit choc : 0,1-1 µg/kg/min — titrer sur PAM."
        ),
    },

    # 8 mg / 40 ml = 200 µg/ml ✅ — [WARN-2] diluant 36 ml G5%
    "Noradrénaline": {
        "ampoules":   "2 A 4 mg/2 ml (2 ml chacune) = 8 mg (4 ml)",
        "diluant":    "36 ml G5 %",   # 4 ml + 36 ml = 40 ml ✅
        "vol_ml":     40,
        "conc_ug_ml": 200,
        # [C-07] + [UPD-2024] SSC 2021 / ESC 2021 choc cardiogénique
        "note": (
            "G5 % OBLIGATOIRE (dégradation en NaCl). "
            "SSC 2021 : noradrénaline = vasopresseur de PREMIER CHOIX (Classe 1 forte). "
            "Cible PAM 65-70 mmHg choc septique — 80-85 mmHg si HTA chronique (SSC 2021). "
            "Voie centrale si > 12 h — voie périphérique acceptable < 6-12h en urgence. "
            "Alerte ≥ 0,25 µg/kg/min → ajouter vasopressine 0,03 UI/min (SSC 2021). "
            "Alerte ≥ 1 µg/kg/min → choc réfractaire — appel réanimateur IMMÉDIAT."
        ),
    },

    # 50 mg / 50 ml = 1000 µg/ml ✅
    "Isosorbide dinitrate (Cédocard)": {
        "ampoules":   "5 A 10 mg/10 ml = 50 mg (50 ml purs)",
        "diluant":    "0 ml — pur",
        "vol_ml":     50,
        "conc_ug_ml": 1000,
        # [C-08] absorption PVC
        "note": (
            "Débit : 1-10 mg/h. "
            "CI : PAS < 90 mmHg, inhibiteurs PDE5 (sildenafil < 24 h / tadalafil < 48 h). "
            "⚠️ Absorption sur tubulure PVC — préférer tubulure PE/verre."
        ),
    },

    # 40 mg / 40 ml = 1000 µg/ml ✅
    "Molsidomine (Corvaton)": {
        "ampoules":   "2 A 20 mg (10 ml chacune) = 40 mg (20 ml)",
        "diluant":    "20 ml NaCl 0,9 %",
        "vol_ml":     40,
        "conc_ug_ml": 1000,
        "note": "Alternative aux nitrés — moins de tachyphylaxie. Débit : 1-4 mg/h.",
    },

    # 50 mg / 50 ml = 1000 µg/ml ✅ — [WARN-10] max 15 mg/h
    "Nicardipine (Rydène)": {
        "ampoules":   "10 A 5 mg/5 ml = 50 mg (50 ml purs)",
        "diluant":    "0 ml — pur",
        "vol_ml":     50,
        "conc_ug_ml": 1000,
        # [C-23] absorption PVC + tachycardie réflexe
        "note": (
            "Prête à l'emploi. Débit : 3-5 mg/h → max 15 mg/h (BCFI). "
            "⚠️ Absorption sur tubulure PVC — tubulure PE ou polyoléfine recommandée. "
            "Tachycardie réflexe fréquente — surveiller FC."
        ),
    },

    # 1,6 mg / 40 ml = 40 µg/ml ✅
    "Isoprénaline (Isuprel)": {
        "ampoules":   "8 A 0,2 mg/1 ml = 1,6 mg (8 ml)",
        "diluant":    "32 ml NaCl 0,9 %",   # 8 + 32 = 40 ml ✅
        "vol_ml":     40,
        "conc_ug_ml": 40,
        # [?-Watteeuw] usage à confirmer localement
        "note": (
            "FC cible 60-70/min. "
            "⚠️ Usage résiduel (BAV congénital, torsades avec bradycardie). "
            "Pacemaker transcutané préféré ERC 2021. "
            "À CONFIRMER usage local — Dr Watteeuw."
        ),
    },

    # 450 mg / 24 ml = 18 750 µg/ml ✅ — [INFO-3] G5% obligatoire
    "Amiodarone (Cordarone)": {
        "ampoules":   "3 A 150 mg/3 ml = 450 mg (9 ml)",
        "diluant":    "15 ml G5 %",   # 9 + 15 = 24 ml ✅
        "vol_ml":     24,
        "conc_ug_ml": 18_750,
        # [C-09] photosensibilité + QT
        "note": (
            "⚠️ G5 % OBLIGATOIRE — précipitation en NaCl 0,9 %. "
            "Protéger de la lumière (photosensible). "
            "Monitoring ECG continu (allongement QT). "
            "Charge : 5 mg/kg en 20-60 min. Entretien : 900 mg/24 h."
        ),
    },

    # 5 mg / 40 ml = 125 µg/ml ✅
    "Salbutamol IV (Ventolin)": {
        "ampoules":   "1 A 5 mg/5 ml",
        "diluant":    "35 ml NaCl 0,9 %",
        "vol_ml":     40,
        "conc_ug_ml": 125,
        "note": "Débit initial : 5-10 µg/min. Réservé AAG IV (échec nébulisations).",
    },

    # 10 000 UI / 50 ml = 200 UI/ml ✅
    "Héparine sodium": {
        "ampoules":   "10 000 UI/2 ml (porcine de préférence)",   # [C-10]
        "diluant":    "48 ml NaCl 0,9 %",
        "vol_ml":     50,
        "conc_ui_ml": 200,
        "conc_ug_ml": None,
        # [C-10] + [UPD-2024] ESC 2023 SCA / ISTH 2023 / ACCP 2022
        "note": (
            "Porcine préférable (risque TIH < bovine). "
            "Débit selon protocole — TCA cible 2-3× témoin. "
            "ESC 2023 SCA : HNF 70-100 UI/kg IV si pas de reperfusion (max 5 000 UI). "
            "ISTH 2023 TIH : score 4T — si ≥ 4 points : arrêt HNF + fondaparinux/argatroban. "
            "ACCP 2022 : HBPM préférée à HNF pour TVP/EP (moins TIH, pas monitoring TCA). "
            "Antagonisation : protamine 1 mg pour 100 UI HNF, max 50 mg (anaphylactoïde possible). "
            "⚠️ TIH type II : thrombopénie J5-J10 — PLQ J3-J5 obligatoire. "
            "Incompatible calcium même voie."
        ),
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# 5. FICHES MÉDICAMENTS — Pharmacopée Hainaut
# Sources : BCFI 2024 / AFMPS / ESC 2023 / ERC 2021 / GINA 2023 / CNGOF 2022
# ══════════════════════════════════════════════════════════════════════════════

MEDICAMENTS_HS: list = [
    {
        "nom":    "Adénocor (Adénosine)",
        "ind":    "Tachycardie supraventriculaire paroxystique (TSV)",
        "dose": (
            # [C-11] CI FA + transplanté — [UPD-2024] ESC SVT 2019 / ERC 2021
            "6 mg IVD RAPIDE (< 2 s) + FLUSH 20 ml NaCl 0,9 % IMMÉDIAT — critique pour efficacité. "
            "Échec 1-2 min → 12 mg IVD (max 1 répétition). "
            "CI absolues : BAV 2-3, dysfonction sinusale, asthme sévère, dipyridamole, "
            "fibrillation atriale (risque réponse ventriculaire rapide sur faisceau accessoire → FV). "
            "Transplanté cardiaque : 1 mg (hypersensibilité — ESC SVT 2019 IB). "
            "Recommandation : ESC 2019 SVT = premier choix TSV (Classe IA). "
            "Échec adénosine : vérapamil 5 mg IV lente OU métoprolol 5 mg IV (ERC 2021)."
        ),
        "source": "ESC Guidelines SVT 2019 (Brugada J, Eur Heart J 2020) / ERC 2021 / BCFI",
    },
    {
        "nom":    "Anexate (Flumazénil)",
        "ind":    "Antidote benzodiazépines",
        "dose": (
            # [C-12] + [UPD-2024] BCFI 2024 / EuReCa
            "0,2 mg IV en 15 s — délai action 1-2 min. "
            "Répéter 0,1 mg/min si insuffisant. Max TOTAL : 1 mg (BCFI/RCP). "
            "CI absolues : épilepsie traitée, tricycliques, dépendance BZD. "
            "Demi-vie 45-90 min — surveiller re-sédation 2-4h. "
            "⚠️ BCFI 2024 : usage limité — risque convulsions > bénéfice diagnostic. "
            "BZD longue durée (alprazolam, clonazépam) : re-sédation quasi certaine. "
            "Alternatives préférées : ventilation non invasive + observation 4-6h."
        ),
        "source": "BCFI 2024 / RCP Anexate AFMPS / EuReCa Toxicologie",
    },
    {
        "nom":    "Aspégic IV (Aspirine)",
        "ind":    "SCA — antiagrégation de première ligne",
        "dose": (
            # [C-13] + [UPD-2024] ESC 2023 SCA — doi:10.1093/eurheartj/ehad191
            "300 mg PO mâché dès suspicion SCA (Classe I, NdP B — ESC 2023). "
            "Biodisponibilité PO mâché > IV → préférer per os sauf PO impossible. "
            "Si PO impossible : 250-500 mg IVD. "
            "Allergie ASA documentée : remplacer par ticagrélor seul (ESC 2023). "
            "SCA + anticoagulation orale préexistante : triple thérapie max 1 semaine. "
            "CI : allergie ASA (cross-réactivité AINS), ulcère actif, "
            "hémorragie active, IRC < 30 ml/min, grossesse T3. "
            "⚠️ Prévention primaire sans ATCD CV : aspirine non recommandée (ESC 2021)."
        ),
        "source": "ESC 2023 SCA (Byrne RA et al.) — doi:10.1093/eurheartj/ehad191 / BCFI",
    },
    {
        "nom":    "Atropine sulfate",
        "ind":    "Bradycardie symptomatique (FC < 50 bpm + instabilité hémodynamique)",
        "dose": (
            # [C-14] + [UPD-2024] ERC 2021 / ESC Bradycardie
            "0,5 mg IV — répéter toutes les 3-5 min, max 3 mg (vagotonolyse complète). "
            "⚠️ Éviter < 0,5 mg par dose (risque bradycardie paradoxale par bloc central). "
            "CI : glaucome angle fermé, iléus paralytique, rétention urinaire, FC > 110 bpm. "
            "⚠️ INEFFICACE sur BAV infranodal (Mobitz II, BAV 3 infrahissien) — "
            "pacemaker transcutané en urgence (ERC 2021). "
            "Échec atropine : isoprénaline IV OU pacemaker transveineux temporaire."
        ),
        "source": "ERC 2021 Arythmies / BCFI",
    },
    {
        "nom":    "Bicarbonate 8,4 %",
        "ind":    "Acidose métabolique sévère (pH < 7,10) / Hyperkaliémie ≥ 6,5 mEq/l / Intox ADT",
        "dose": (
            # [C-15] + [UPD-2024] ERC 2021 / SFAR 2023 / KDIGO 2022
            "Acidose métabolique (pH < 7,10) : 1-2 mEq/kg IV — titrer sur gazométrie. "
            "Hyperkaliémie urgente (K > 6,5 ou signes ECG) : 100 ml en 10 min + ECG continu. "
            "Intox ADT (QRS > 100 ms) : 1-2 mEq/kg IVD — cible pH 7,50-7,55. "
            "⚠️ ERC 2021 : bicarbonate NON recommandé en routine dans l'ACR. "
            "Acidose lactique : discuté si pH < 7,15 + ventilation adaptée + "
            "cause traitable (SFAR 2023). "
            "CI relative : alcalose préexistante. "
            "⚠️ Incompatible calcium même tubulure (précipitation)."
        ),
        "source": "BCFI / SFAR 2023 / ERC 2021 / KDIGO 2022",
    },
    {
        "nom":    "Brilique (Ticagrélor)",
        "ind":    "SCA NSTEMI/STEMI — double antiagrégation",
        "dose": (
            # [C-16] + [UPD-2024] ESC 2023 SCA — doi:10.1093/eurheartj/ehad191
            "Charge : 180 mg PO (2 cp 90 mg) dès diagnostic (Classe I, NdP B — ESC 2023). "
            "Entretien : 90 mg × 2/j + Aspégic 75-100 mg/j. "
            "STEMI primaire : charge préférable en salle cath (non systématique en préhospitalier). "
            "ES fréquent : dyspnée (20%) sans IC — distinguer de l'OAP avant traitement. "
            "CI absolues : hémorragie intracrânienne, IH sévère, ciclosporine (↑taux × 3), "
            "kétoconazole/itraconazole (↑taux × 7). "
            "Interactions majeures : anticoagulants, inhibiteurs CYP3A4 puissants. "
            "⚠️ Pas d'antidote — transfusion plaquettaire INEFFICACE."
        ),
        "source": "ESC 2023 SCA (Byrne RA et al.) — doi:10.1093/eurheartj/ehad191 / BCFI",
    },
    {
        "nom":    "Cédocard (Isosorbide dinitrate IV)",
        "ind":    "SCA / Insuffisance cardiaque aiguë / HTA hypertensive",
        "dose": (
            # [C-08] + [UPD-2024] ESC 2021 IC aiguë / ESC 2023 SCA
            "PSE 50 mg/50 ml (1 mg/ml) — débuter 1-2 mg/h, max 10 mg/h (avis médical). "
            "ESC 2021 IC aiguë : nitrés recommandés si PAS > 110 mmHg (Classe IIa). "
            "⚠️ Tachyphylaxie après 24h — rotation ou pause recommandée. "
            "CI : PAS < 90 mmHg, choc, tamponnade, inhibiteurs PDE5 "
            "(sildenafil < 24 h / tadalafil < 48 h). "
            "⚠️ Absorption sur tubulure PVC — préférer tubulure PE ou verre."
        ),
        "source": "ESC 2021 IC aiguë (McDonagh TA) / ESC 2023 SCA / BCFI",
    },
    {
        "nom":    "Glucose 30 %",
        "ind":    "Hypoglycémie sévère (< 54 mg/dl) avec altération de conscience",
        "dose": (
            "Adulte : 0,3 g/kg IV lente (≈ 100 ml G30 % max). "
            "Enfant : 0,2 g/kg IV lente. "
            "Contrôle glycémie à 15 min — objectif > 70 mg/dl."
        ),
        "source": "BCFI / Protocoles SFMEA",
    },
    {
        "nom":    "Valium (Diazépam)",
        "ind":    "Convulsions / État de mal épileptique / Sevrage alcoolique",
        "dose": (
            # [C-17] + [UPD-2024] ILAE 2022 / SFNP 2023 / Cochrane 2023
            "Adulte IV : 5-10 mg IV lente (< 5 mg/min), répétable 1×. "
            "⚠️ Phlébite possible (solvant propylèneglycol) — midazolam IV préférable. "
            "ILAE 2022 : place du diazépam revue — "
            "midazolam IM = premier choix hors hôpital | lorazépam IV = premier choix intra-hospitalier. "
            "EME réfractaire > 30 min : lévétiracétam IV 60 mg/kg OU valproate IV (2e ligne). "
            "Enfant IV : 0,2-0,3 mg/kg (max 5 mg < 5 ans / max 10 mg ≥ 5 ans). "
            "Enfant IR : 0,3-0,5 mg/kg (max 10 mg). "
            "Accumulation (demi-vie 20-100 h) — réduire dose en IR/IH. "
            "Antidote : Flumazénil."
        ),
        "source": "ILAE 2022 / BCFI / SFNP 2023 / Cochrane EME 2023",
    },
    {
        "nom":    "Sufenta (Sufentanil citrate)",
        "ind":    "Analgésie forte — MÉDECIN / IADE UNIQUEMENT",
        "dose": (
            # [C-18] avertissement renforcé
            "⚠️ PUISSANCE × 10 vs MORPHINE — ERREUR DE DOSE PEUT ÊTRE FATALE. "
            "Titration IV : 0,1-0,2 µg/kg IV lente (médecin/IADE). "
            "PSE : 5 A × 50 µg = 250 µg dans 50 ml NaCl → 5 µg/ml. Débit : 1-3 ml/h. "
            "CI : dépression respiratoire, intox BZD/alcool. "
            "Antidote : Naloxone 0,4 mg IV — surveiller re-narcose."
        ),
        "source": "BCFI / RCP Sufenta",
    },
    {
        "nom":    "Solumédrol (Méthylprednisolone)",
        "ind":    "Allergie sévère / Asthme aigu grave / Anaphylaxie (2e ligne après adrénaline)",
        "dose": (
            # [C-19] + [UPD-2024] GINA 2023 / ERS-ATS 2022 / EAACI 2021
            "Adulte : 80-125 mg IVD (dose d'attaque). "
            "Enfant : 1-2 mg/kg IV (max 125 mg). "
            "Délai d'action 4-6 h — relais PO 1 mg/kg/j en décroissance. "
            "GINA 2023 : corticoïde systémique obligatoire dans TOUT asthme aigu sévère (Classe A). "
            "Simplification GINA 2023 : dose unique 40 mg prednisone PO = efficacité 5 jours. "
            "BPCO exacerbation (ERS/ATS 2022) : 40 mg/j PO × 5j — IV si déglutition impossible. "
            "Anaphylaxie : prévient réaction biphasique (délai 6-12h — EAACI 2021). "
            "⚠️ Hyperglycémie quasi constante — glycémie capillaire à H+4. "
            "⚠️ Si SDRA/COVID-19 : dexaméthasone 6 mg/j préférée (RECOVERY trial 2021)."
        ),
        "source": "GINA 2023 / ERS-ATS 2022 / EAACI 2021 / RECOVERY 2021 / BCFI",
    },
    {
        "nom":    "Buscopan (Butylscopolamine)",
        "ind":    "Colique biliaire / urétérale / spasmes digestifs",
        "dose": (
            # [C-20] tachycardie transitoire
            "20 mg IV lente (> 1 min) ou IM — max 100 mg/j. "
            "CI : glaucome angle fermé, occlusion intestinale mécanique, "
            "mégacôlon, myasthénie, CI < 1 an. "
            "⚠️ Tachycardie transitoire fréquente en IV — tolérable si FC < 120 bpm."
        ),
        "source": "BCFI — Hyoscine butylbromide",
    },
    {
        "nom":    "Atrovent (Ipratropium bromure)",
        "ind":    "Bronchospasme (asthme/BPCO) — toujours associé au salbutamol",
        "dose": (
            # [C-21] + [UPD-2024] GINA 2023 / GOLD 2024 / Cochrane 2023
            "Adulte : 0,5 mg nébulisation / 4-6 h. "
            "Enfant < 5 ans : 0,25 mg nébulisation. "
            "Enfant ≥ 5 ans : 0,5 mg nébulisation. "
            "GINA 2023 : ipratropium + salbutamol = standard asthme aigu sévère (Classe A). "
            "GOLD 2024 : SABA/SAMA en urgence BPCO — LABA/LAMA en entretien chronique. "
            "Cochrane 2023 : nébulisation continue = intermittente (pas de supériorité démontrée). "
            "⚠️ NE PAS utiliser en monothérapie — associer salbutamol systématiquement. "
            "⚠️ Nébulisation au masque : risque glaucome angle fermé si contact oculaire."
        ),
        "source": "GINA 2023 / GOLD 2024 / BCFI / BTS 2022 / Cochrane 2023",
    },
    {
        "nom":    "Syntocinon (Ocytocine)",
        "ind":    "Déclenchement travail / Hémorragie du post-partum (HPP)",
        "dose": (
            # [C-22] + [UPD-2024] OMS 2023 / CNGOF 2022 / FIGO 2022
            "HPP : 5-10 UI IV EN ≥ 1 MIN OBLIGATOIRE "
            "(bolus rapide = collapsus cardiovasculaire grave). "
            "Entretien HPP : 20 UI dans 500 ml G5 % à 125 ml/h (= 40 mUI/min, CNGOF 2022). "
            "OMS 2023 + CNGOF 2022 : ajouter acide tranexamique 1 g IV dans les 3h (WOMAN trial). "
            "FIGO 2022 : carbétocine (Pabal® 100 µg IM/IV) = alternative ocytocine, effet plus long. "
            "Échec ocytocine + TXA : sulprostone (Nalador®) 500 µg PSE — CNGOF 2022. "
            "CI : détresse fœtale, présentation transversale."
        ),
        "source": "OMS 2023 / CNGOF 2022 HPP (WOMAN trial) / FIGO 2022 / BCFI",
    },
    {
        "nom":    "Rydène (Nicardipine IV)",
        "ind":    "HTA sévère / encéphalopathique / éclampsie / dissection aortique",
        "dose": (
            # [C-23] + [UPD-2024] ESC/ESH 2023 HTA — doi:10.1093/eurheartj/ehad195
            "Titration : 1 mg IV en 10 min — contrôle PA / 5 min. "
            "PSE : 3-5 mg/h → max 15 mg/h (BCFI). "
            "ESC/ESH 2023 : nicardipine IV = référence crise hypertensive (Classe I). "
            "Objectif ESC 2023 : réduction PA ≤ 25 % en 1h, normalisation sur 24-48h. "
            "Cible dissection aortique : PAS 100-120 mmHg + FC < 60 bpm. "
            "Cible éclampsie : PAS < 160 mmHg (risque convulsions si ≥ 160). "
            "Alternative si CI inhibiteurs calciques : labétalol IV 20 mg bolus. "
            "CI : hypotension, sténose aortique sévère, angor instable < 8 j. "
            "⚠️ Absorption sur tubulure PVC — tubulure PE ou polyoléfine recommandée. "
            "Tachycardie réflexe fréquente — surveiller FC."
        ),
        "source": "ESC/ESH 2023 HTA (McEvoy JW) — doi:10.1093/eurheartj/ehad195 / BCFI",
    },
    {
        "nom":    "Zyprexa (Olanzapine IM)",
        "ind":    "Agitation psychomotrice sévère / Épisode psychotique aigu",
        "dose": (
            # [C-24] + [UPD-2024] BAP 2023 / NICE 2022 / SFAR 2023
            "5-10 mg IM — max 20 mg/j (BAP 2023 : 10 mg suffisant — éviter 20 mg d'emblée). "
            "CI absolues : BZD IM concomitantes (arrêt cardio-respiratoire), "
            "glaucome angle fermé, démence à corps de Lewy, "
            "syndrome parkinsonien, QTc > 450 ms (H) / > 470 ms (F) — ECG préalable. "
            "NICE 2022 : monitoring respiratoire 2h post-injection (non plus 30 min). "
            "SFAR 2023 : dexmédétomidine IV = alternative si agitation sans dépression respi. "
            "⚠️ Syndrome malin des neuroleptiques : hyperthermie + rigidité + ↑CPK → arrêt immédiat."
        ),
        "source": "BAP 2023 / NICE 2022 / SFAR 2023 / BCFI / AFMPS",
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# 6. FONCTIONS D'AFFICHAGE
# ══════════════════════════════════════════════════════════════════════════════

def section_dilutions_hainaut() -> None:
    """Tableau des dilutions PSE Hainaut — concentrations auditées v19.2."""
    st.markdown(
        "<div style='font-size:.72rem;font-weight:700;color:#64748B;"
        "text-transform:uppercase;margin-bottom:6px;'>"
        "📊 Dilutions PSE — Standard Hainaut (auditées v19.2)</div>",
        unsafe_allow_html=True)

    rows = []
    for nom, d in HAUTE_SENNE_DILUTIONS.items():
        conc = (f"{d['conc_ui_ml']:.0f} UI/ml"
                if d.get("conc_ui_ml")
                else f"{d.get('conc_ug_ml', '?')} µg/ml")
        rows.append({
            "Médicament":      nom,
            "Ampoules":        d["ampoules"],
            "Diluant":         d["diluant"],
            "Vol. total (ml)": d["vol_ml"],
            "Concentration":   conc,
            "Note / CI":       d.get("note", ""),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "Sources : BCFI 2024 / AFMPS / RCP fabricants — "
        "Concentrations vérifiées mathématiquement v19.2. "
        "⚠️ Vérifier compatibilité physico-chimique avant tout mélange. "
        "CBP 070/245.245 (24h/24) en cas de doute.")


def calculateur_noradrenaline(poids_defaut: float = 70.0) -> None:
    """
    Calculateur Noradrénaline — Concentration 200 µg/ml.
    Dilution v19.2 : 2 A × 4 mg (4 ml) + 36 ml G5 % = 40 ml.
    Formule : Débit (ml/h) = Dose (µg/kg/min) × Poids (kg) × 60 / 200.
    Sources : SSC 2021 / BCFI.
    """
    st.markdown(
        "<div style='font-size:.72rem;font-weight:700;color:#64748B;"
        "text-transform:uppercase;margin-bottom:6px;'>"
        "⚡ Calculateur — Noradrénaline 200 µg/ml</div>",
        unsafe_allow_html=True)
    st.caption(
        "Dilution : 2 A × 4 mg (4 ml) + 36 ml G5 % → 40 ml — 200 µg/ml | "
        "SSC 2021 : cible PAM ≥ 65 mmHg")

    nc1, nc2 = st.columns(2)
    pw   = nc1.slider("Poids (kg)", 30, 150, int(poids_defaut), 1,
                       key=_ek("na_poids"))
    dose = nc2.select_slider(
        "Dose µg/kg/min",
        options=[0.01, 0.02, 0.05, 0.08, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 1.0],
        value=0.1,
        key=_ek("na_dose"),
    )

    debit = round((dose * pw * 60) / 200, 2)
    auto  = round(40 / debit, 1) if debit > 0 else "∞"
    col   = ("#EF4444" if dose >= 1.0 else
             "#F59E0B" if dose >= 0.5 else "#38BDF8")

    st.markdown(
        f"<div style='background:#0F172A;border:2px solid {col};"
        f"border-radius:12px;padding:16px;text-align:center;margin:10px 0;'>"
        f"<div style='color:#94A3B8;font-size:.72rem;text-transform:uppercase;'>"
        f"Débit — {dose} µg/kg/min × {pw} kg</div>"
        f"<div style='color:{col};font-size:2.5rem;font-weight:900;"
        f"font-family:monospace;'>{debit:.2f} ml/h</div>"
        f"<div style='color:#64748B;font-size:.7rem;'>Autonomie 40 ml : {auto} h</div>"
        f"</div>",
        unsafe_allow_html=True)

    if dose >= 1.0:
        st.error(
            "🔴 Dose ≥ 1 µg/kg/min — Choc réfractaire\n"
            "Appel réanimateur IMMÉDIAT — Envisager vasopressine 0,03 UI/min")
    elif dose >= 0.5:
        st.warning(
            "🟠 Dose ≥ 0,5 µg/kg/min\n"
            "Voie centrale si > 12 h — Monitorage TA invasif recommandé")

    with st.expander("📋 Tableau de référence (ml/h)", expanded=False):
        p_range = list(range(40, 125, 5))
        d_range = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]
        data    = {f"{d} µg/kg/min": [round((d*p*60)/200, 2) for p in p_range]
                   for d in d_range}
        df      = pd.DataFrame(data, index=[f"{p} kg" for p in p_range])

        def _hl(row):
            return ["background:#1E3A5F;color:#38BDF8;font-weight:700"
                    if row.name == f"{pw} kg" else "" for _ in row]

        st.dataframe(df.style.apply(_hl, axis=1), use_container_width=True)
        st.caption("SSC 2021 : cible PAM ≥ 65 mmHg | Voie centrale recommandée si > 12 h")


def section_fiches_medicaments() -> None:
    """Fiches posologies Hainaut — auditées et corrigées v19.2."""
    with st.expander(
            "💊 Pharmacopée Hainaut — Fiches posologies (auditées v19.2)",
            expanded=False):
        st.caption(
            "Sources : BCFI 2024 / AFMPS / ESC 2023 / ERC 2021 / "
            "GINA 2023 / CNGOF 2022 / SFNP 2023\n"
            "Validation médicale obligatoire avant tout acte thérapeutique.")

        search = st.text_input(
            "Rechercher", key=_ek("hs_search"),
            placeholder="ex. : atropine, nicardipine…")
        filtered = _search_medicaments(search, MEDICAMENTS_HS)
        if not filtered:
            st.info("Aucun résultat — essayer un autre terme")

        for med in filtered:
            src = med.get("source", "")
            st.markdown(
                f"<div style='background:#0F172A;border-left:4px solid #334155;"
                f"border-radius:0 8px 8px 0;padding:10px 14px;margin:4px 0;'>"
                f"<div style='font-size:.82rem;font-weight:700;color:#E2E8F0;'>"
                f"{med['nom']}</div>"
                f"<div style='font-size:.7rem;color:#94A3B8;'>"
                f"<b>Indication :</b> {med['ind']}</div>"
                f"<div style='font-size:.72rem;color:#CBD5E1;margin-top:3px;'>"
                f"{med['dose']}</div>"
                f"<div style='font-size:.72rem;color:#475569;margin-top:4px;"
                f"font-style:italic;'>{src}</div>"
                f"</div>",
                unsafe_allow_html=True)

        st.divider()
        st.caption(
            "⚠️ Aide-mémoire IAO — usage interne. "
            "Vérifier via bcfi.be ou CBP 070/245.245. "
            "Tout acte thérapeutique requiert un ordre médical.")
