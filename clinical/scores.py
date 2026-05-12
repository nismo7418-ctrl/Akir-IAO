# clinical/scores.py — Scores cliniques validés — AKIR-IAO v20
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Chaque fonction retourne un dict standardisé :
#   {score_val, interpretation, recommendation, citations_medicales}

from __future__ import annotations
from typing import Dict, List, Optional


def _result(score_val, interpretation: str, recommendation: str,
            citations: List[str]) -> Dict:
    """Constructeur standardisé pour tous les scores."""
    return {
        "score_val": score_val,
        "interpretation": interpretation,
        "recommendation": recommendation,
        "citations_medicales": citations,
    }


def calculer_gcs(ouverture_yeux: int, reponse_verbale: int, reponse_motrice: int, age: float = 18.0) -> Dict:
    """GCS adulte/pédiatrique. Source: Teasdale & Jennett, Lancet 1974."""
    try:
        score = max(3, min(15, int(ouverture_yeux) + int(reponse_verbale) + int(reponse_motrice)))
        if score <= 8:
            return _result(score, f"GCS {score} — Coma", "Intubation à discuter — Appel médical IMMÉDIAT", ["Teasdale G & Jennett B, Lancet 1974"])
        elif score <= 12:
            return _result(score, f"GCS {score} — Altération modérée", "Surveillance neurologique rapprochée — Tri ≤ 2", ["Teasdale G & Jennett B, Lancet 1974"])
        elif score == 13:
            return _result(score, f"GCS {score} — Légère altération", "Réévaluation neurologique < 30 min", ["Teasdale G & Jennett B, Lancet 1974"])
        return _result(score, f"GCS {score} — Conscience normale", "Surveillance standard", ["Teasdale G & Jennett B, Lancet 1974"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def calculer_qsofa(fr: float, gcs: int, pas: float) -> Dict:
    """qSOFA sepsis. Source: Seymour CW et al., JAMA 2016."""
    try:
        score = 0
        criteres = []
        if float(fr) >= 22: score += 1; criteres.append(f"FR {fr}/min")
        if int(gcs) < 15:   score += 1; criteres.append(f"GCS {gcs}")
        if float(pas) <= 100: score += 1; criteres.append(f"PAS {pas} mmHg")
        if score >= 2:
            return _result(score, f"qSOFA {score}/3 — SEPSIS SUSPECTÉ ({', '.join(criteres)})", "Bundle Sepsis 1h — Hémocultures, lactates, antibio — Tri 2", ["Seymour CW et al., JAMA 2016"])
        elif score == 1:
            return _result(score, f"qSOFA {score}/3 — Vigilance", "Surveillance rapprochée — Réévaluer", ["Seymour CW et al., JAMA 2016"])
        return _result(0, "qSOFA 0/3 — Sepsis peu probable", "Réévaluation si contexte évocateur", ["Seymour CW et al., JAMA 2016"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def calculer_heart(history: int, ecg: int, age: int, risk_factors: int, troponin: int) -> Dict:
    """HEART Score SCA. Source: Six AJ et al., NHJ 2008."""
    try:
        score = max(0, min(10, sum([int(history), int(ecg), int(age), int(risk_factors), int(troponin)])))
        if score <= 3:
            return _result(score, f"HEART {score} — Risque faible (MACE < 2 %)", "Sortie possible après obs 3h", ["Six AJ et al., Neth Heart J 2008"])
        elif score <= 6:
            return _result(score, f"HEART {score} — Risque intermédiaire (MACE ~15 %)", "Hospitalisation — Troponines sériées", ["Six AJ et al., Neth Heart J 2008"])
        return _result(score, f"HEART {score} — Risque élevé (MACE > 50 %)", "Revascularisation urgente — Cardiologue IMMÉDIAT", ["Six AJ et al., Neth Heart J 2008"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def calculer_timi(
    age_65: bool,          # 1pt — Âge ≥ 65 ans
    risk_factors: bool,    # 1pt — ≥ 3 facteurs de risque CV (HTA, DT, tabac, dyslipidémie, ATCD familial)
    coronaropathie: bool,  # 1pt — Sténose coronaire connue ≥ 50 %
    ecg: bool,             # 1pt — Déviation ST à l'ECG d'admission
    angine_severe: bool,   # 1pt — ≥ 2 épisodes angineux dans les 24h
    aspirine: bool,        # 1pt — Prise d'aspirine dans les 7 jours précédents
    marqueurs: bool,       # 1pt — Élévation des marqueurs cardiaques (troponine)
) -> Dict:
    """TIMI Risk Score UA/NSTEMI (0-7).
    
    Risque d'événements majeurs (MACE) à 14 jours :
    0-2 pts : 4.7 %  |  3-4 pts : 13.2 %  |  5-7 pts : 40.9 %
    Source: Antman EM et al., JAMA 2000 — doi:10.1001/jama.284.7.835
    """
    try:
        score = sum([int(age_65), int(risk_factors), int(coronaropathie),
                     int(ecg), int(angine_severe), int(aspirine), int(marqueurs)])
        if score == 0:
            return _result(0, "TIMI 0 — Risque très faible (MACE < 2 %)", 
                          "Sortie précoce possible après observation 3h + troponines sériées", 
                          ["Antman EM et al., JAMA 2000"])
        elif score <= 2:
            return _result(score, f"TIMI {score} — Risque faible (MACE ~5 %)", 
                          "Stratégie conservatrice — Observation 6-12h — Troponines × 2",
                          ["Antman EM et al., JAMA 2000"])
        elif score <= 4:
            return _result(score, f"TIMI {score} — Risque intermédiaire (MACE ~13 %)", 
                          "Coronarographie dans les 24-48h — HBPM + antiagrégant",
                          ["Antman EM et al., JAMA 2000"])
        return _result(score, f"TIMI {score} — Risque élevé (MACE ~41 %)", 
                      "Coronarographie urgente < 24h — Appel cardiologue immédiat",
                      ["Antman EM et al., JAMA 2000"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def calculer_wells_tvp(cancer: bool, immobilisation: bool, chirurgie: bool, sensibilite_trajet: bool, oedeme_godet: bool, asymetrie_mollet: bool, asymetrie_membre: bool, veines_collaterales: bool, antecedent_tvp: bool, diagnostic_alternatif: bool) -> Dict:
    """Wells TVP. Source: Wells PS et al., Lancet 1997."""
    try:
        score = (int(cancer) + int(immobilisation) + int(chirurgie) + int(sensibilite_trajet) + int(oedeme_godet) + int(asymetrie_mollet) + int(asymetrie_membre) + int(veines_collaterales) + int(antecedent_tvp) - (2 if diagnostic_alternatif else 0))
        if score <= 0:
            return _result(score, f"Wells TVP {score} — Faible", "D-Dimères — si négatifs TVP exclue", ["Wells PS et al., Lancet 1997"])
        elif score <= 2:
            return _result(score, f"Wells TVP {score} — Modérée", "D-Dimères et/ou écho-Doppler", ["Wells PS et al., Lancet 1997"])
        return _result(score, f"Wells TVP {score} — Élevée", "Écho-Doppler URGENT — Anticoagulation", ["Wells PS et al., Lancet 1997"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def calculer_wells_ep(tvp_symptomes: bool, ep_plus_probable: bool, fc_100: bool, immobilisation: bool, antecedent: bool, hemoptysie: bool, cancer: bool) -> Dict:
    """Wells EP. Source: Wells PS et al., Thromb Haemost 2000."""
    try:
        score = ((3.0 if tvp_symptomes else 0) + (3.0 if ep_plus_probable else 0) + (1.5 if fc_100 else 0) + (1.5 if immobilisation else 0) + (1.5 if antecedent else 0) + (1.0 if hemoptysie else 0) + (1.0 if cancer else 0))
        if score <= 1:
            return _result(score, f"Wells EP {score} — Faible", "PERC rule — si négatif D-Dimères", ["Wells PS et al., Thromb Haemost 2000"])
        elif score <= 4:
            return _result(score, f"Wells EP {score} — Modérée", "D-Dimères — si positifs angio-TDM", ["Wells PS et al., Thromb Haemost 2000"])
        return _result(score, f"Wells EP {score} — Élevée", "Angio-TDM URGENT — Anticoagulation empirique", ["Wells PS et al., Thromb Haemost 2000"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def calculer_nihss(conscience: int, questions: int, ordres: int, oculomotricite: int, champ_visuel: int, facial: int, motricite_bras_g: int, motricite_bras_d: int, motricite_jambe_g: int, motricite_jambe_d: int, ataxie: int, sensibilite: int, langage: int, dysarthrie: int, extinction: int) -> Dict:
    """NIHSS AVC. Source: Brott T et al., Stroke 1989."""
    try:
        score = sum([conscience, questions, ordres, oculomotricite, champ_visuel, facial, motricite_bras_g, motricite_bras_d, motricite_jambe_g, motricite_jambe_d, ataxie, sensibilite, langage, dysarthrie, extinction])
        if score == 0:
            return _result(0, "NIHSS 0 — Normal", "Surveiller — AIT possible", ["Brott T et al., Stroke 1989"])
        elif score <= 4:
            return _result(score, f"NIHSS {score} — AVC mineur", "Thrombolyse à discuter — IRM urgente", ["Brott T et al., Stroke 1989"])
        elif score <= 15:
            return _result(score, f"NIHSS {score} — AVC modéré", "Thrombolyse si ≤ 4h30 — Thrombectomie", ["Brott T et al., Stroke 1989"])
        elif score <= 20:
            return _result(score, f"NIHSS {score} — AVC sévère", "Thrombectomie — Unité neurovasculaire URGENTE", ["Brott T et al., Stroke 1989"])
        return _result(score, f"NIHSS {score} — AVC très sévère", "Soins intensifs neurovasculaires", ["Brott T et al., Stroke 1989"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def calculer_sofa_partiel(pao2_fio2: Optional[float], plaquettes: Optional[float], bilirubine: Optional[float], pas: float, gcs: int, creatinine: Optional[float]) -> Dict:
    """SOFA partiel urgences. Source: Singer M et al., JAMA 2016."""
    try:
        score = 0
        if pao2_fio2 is not None:
            if pao2_fio2 < 100: score += 4
            elif pao2_fio2 < 200: score += 3
            elif pao2_fio2 < 300: score += 2
            elif pao2_fio2 < 400: score += 1
        if plaquettes is not None:
            if plaquettes < 20: score += 4
            elif plaquettes < 50: score += 3
            elif plaquettes < 100: score += 2
            elif plaquettes < 150: score += 1
        if pas <= 70: score += 3
        elif pas <= 90: score += 1
        if gcs < 6: score += 4
        elif gcs < 10: score += 3
        elif gcs < 13: score += 2
        elif gcs < 15: score += 1
        if creatinine is not None:
            if creatinine > 440: score += 4
            elif creatinine > 300: score += 3
            elif creatinine > 170: score += 2
            elif creatinine > 110: score += 1
        if score >= 11:
            return _result(score, f"SOFA {score} — Défaillance multiviscérale", "Réanimation — Mortalité > 50 %", ["Singer M et al., JAMA 2016"])
        elif score >= 7:
            return _result(score, f"SOFA {score} — Dysfonction sévère", "Soins intensifs — Réanimateur urgent", ["Singer M et al., JAMA 2016"])
        elif score >= 3:
            return _result(score, f"SOFA {score} — Dysfonction modérée", "Bundle sepsis 1h", ["Singer M et al., JAMA 2016"])
        return _result(score, f"SOFA {score} — Léger", "Bilan complet — Réévaluation", ["Singer M et al., JAMA 2016"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def calculer_curb65(confusion: bool, uree_7: bool, fr_30: bool, pas_90_pad_60: bool, age_65: bool) -> Dict:
    """CURB-65 pneumonie. Source: Lim WS et al., Thorax 2003."""
    try:
        score = sum([int(confusion), int(uree_7), int(fr_30), int(pas_90_pad_60), int(age_65)])
        if score <= 1:
            return _result(score, f"CURB-65 {score} — Légère (mortalité < 3 %)", "Traitement ambulatoire", ["Lim WS et al., Thorax 2003"])
        elif score == 2:
            return _result(score, f"CURB-65 {score} — Modérée (~9 %)", "Hospitalisation courte", ["Lim WS et al., Thorax 2003"])
        elif score == 3:
            return _result(score, f"CURB-65 {score} — Sévère (~17 %)", "Hospitalisation — Soins aigus", ["Lim WS et al., Thorax 2003"])
        return _result(score, f"CURB-65 {score} — Très sévère (≥ 30 %)", "Soins intensifs — Avis réanimateur", ["Lim WS et al., Thorax 2003"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def evaluer_fast(face: bool, arm: bool, speech: bool, time: str, balance: bool = False, eyes: bool = False) -> Dict:
    """BE-FAST AVC. Source: Kothari RU et al., Ann Emerg Med 1999."""
    try:
        positifs = sum([int(balance), int(eyes), int(face), int(arm), int(speech)])
        if positifs >= 1:
            return _result(positifs, f"BE-FAST POSITIF ({positifs} signe(s)) — AVC SUSPECTÉ", f"CODE STROKE IMMÉDIAT — Dernière fois vu bien : {time or 'inconnue'}", ["Kothari RU et al., Ann Emerg Med 1999"])
        return _result(0, "BE-FAST négatif — AVC moins probable", "NIHSS si doute clinique", ["Kothari RU et al., Ann Emerg Med 1999"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def calculer_algoplus(visage: bool, regard: bool, plaintes: bool, attitudes: bool, comportement: bool) -> Dict:
    """Algoplus non-communicant. Source: Rat P et al., Eur J Pain 2011."""
    try:
        score = sum([int(visage), int(regard), int(plaintes), int(attitudes), int(comportement)])
        if score >= 2:
            return _result(score, f"Algoplus {score}/5 — Douleur significative", "Antalgie adaptée — Réévaluation 30 min (Circulaire belge 2014)", ["Rat P et al., Eur J Pain 2011"])
        return _result(score, f"Algoplus {score}/5 — Absent/léger", "Surveiller — Réévaluer si changement", ["Rat P et al., Eur J Pain 2011"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def evaluer_cfs(niveau: int) -> Dict:
    """CFS fragilité. Source: Rockwood K et al., CMAJ 2005."""
    desc = {1:"Très robuste",2:"Bien portant",3:"Bien portant avec maladies traitées",4:"Vulnérable",5:"Légèrement fragile",6:"Modérément fragile",7:"Sévèrement fragile",8:"Très sévèrement fragile",9:"En phase terminale"}
    try:
        n = max(1, min(9, int(niveau)))
        if n >= 7:
            return _result(n, f"CFS {n} — {desc[n]} — Fragilité sévère", "Évaluation gériatrique — Réanimation à discuter", ["Rockwood K et al., CMAJ 2005"])
        elif n >= 5:
            return _result(n, f"CFS {n} — {desc[n]} — Fragilité modérée", "Adapter les doses — Interactions médicamenteuses", ["Rockwood K et al., CMAJ 2005"])
        return _result(n, f"CFS {n} — {desc[n]}", "Prise en charge standard", ["Rockwood K et al., CMAJ 2005"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def regle_ottawa_cheville(douleur_malleole_post_d: bool, douleur_malleole_post_g: bool, douleur_base_5e: bool, douleur_naviculaire: bool, incapacite_appui: bool) -> Dict:
    """Ottawa cheville/pied. Source: Stiell IG et al., JAMA 1993."""
    try:
        radio_cheville = (douleur_malleole_post_d or douleur_malleole_post_g) and incapacite_appui
        radio_pied = (douleur_base_5e or douleur_naviculaire) and incapacite_appui
        if radio_cheville or radio_pied:
            zones = []
            if radio_cheville: zones.append("cheville")
            if radio_pied: zones.append("pied")
            return _result(1, f"Ottawa POSITIF — Radio {' + '.join(zones)} indiquée", f"Radio {' + '.join(zones)}", ["Stiell IG et al., JAMA 1993"])
        return _result(0, "Ottawa NÉGATIF — Fracture peu probable", "Pas de radio — Traitement symptomatique", ["Stiell IG et al., JAMA 1993"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


def regle_canadian_ct(gcs_sous_15: bool, fracture_ouverte: bool, fracture_base: bool, vomissements: bool, age_65: bool, amnesie_30min: bool, mecanisme_dangereux: bool) -> Dict:
    """Canadian CT Head. Source: Stiell IG et al., Lancet 2001."""
    try:
        haut = any([gcs_sous_15, fracture_ouverte, fracture_base, vomissements, age_65])
        moyen = any([amnesie_30min, mecanisme_dangereux])
        if haut:
            return _result(2, "Canadian CT — HAUT RISQUE", "TDM cérébral URGENT", ["Stiell IG et al., Lancet 2001"])
        elif moyen:
            return _result(1, "Canadian CT — RISQUE MOYEN", "TDM cérébral recommandé", ["Stiell IG et al., Lancet 2001"])
        return _result(0, "Canadian CT — RISQUE FAIBLE", "TDM non obligatoire — Surveillance clinique", ["Stiell IG et al., Lancet 2001"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


# ─────────────────────────────────────────────────────────────────────────────
# ABCD2 — Risque AVC après AIT (48h et 7j)
# Source : Johnston SC et al., Lancet 2007.
# Pertinence IAO : tout déficit transitoire doit être stratifié
# ─────────────────────────────────────────────────────────────────────────────

def calculer_abcd2(
    age_60: bool,
    hta: bool,
    type_clinique: str,   # "hemiplegie" | "trouble_parole" | "autre"
    duree_min: float,     # durée des symptômes en minutes
    diabete: bool,
) -> Dict:
    """
    ABCD2 Score (0-7) — Risque d'AVC dans les 2j et 7j après un AIT.
    Recommandé par l'ESO 2023 pour la stratification rapide aux urgences.
    Source : Johnston SC et al., Lancet 2007.
    """
    try:
        score = 0
        # A — Âge ≥ 60 ans
        if age_60: score += 1
        # B — Blood pressure : PAS ≥ 140 ou PAD ≥ 90
        if hta: score += 1
        # C — Clinical features
        if type_clinique == "hemiplegie":
            score += 2
        elif type_clinique == "trouble_parole":
            score += 1
        # D — Duration
        if duree_min >= 60:
            score += 2
        elif duree_min >= 10:
            score += 1
        # D2 — Diabetes
        if diabete: score += 1

        # Risque AVC à 2j selon Johnston 2007
        risque_2j = {0:0,1:0,2:0,3:1.3,4:4.0,5:8.1,6:11.7,7:11.7}.get(min(score,7), 0)
        risque_7j = {0:0,1:0,2:0,3:1.3,4:4.1,5:12.1,6:17.8,7:21.7}.get(min(score,7), 0)

        if score >= 4:
            interp = f"ABCD2 {score} — RISQUE ÉLEVÉ (AVC à 2j : {risque_2j}%)"
            reco   = "Hospitalisation urgente — IRM DWI < 24h — Antiagrégant + statine"
        elif score >= 3:
            interp = f"ABCD2 {score} — Risque modéré (AVC à 2j : {risque_2j}%)"
            reco   = "Évaluation rapide < 24h — IRM cérébrale — Doppler carotidien"
        else:
            interp = f"ABCD2 {score} — Risque faible (AVC à 2j : {risque_2j}%)"
            reco   = "Évaluation dans les 24-48h — Bilan étiologique"

        return _result(score, interp, reco,
                       ["Johnston SC et al., Lancet 2007",
                        "ESO Guidelines AIT/AVC 2023"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


# ─────────────────────────────────────────────────────────────────────────────
# PERC Rule — Exclusion EP sans dosage D-Dimères
# Source : Kline JA et al., J Thromb Haemost 2004.
# Applicable si Wells EP ≤ 1 ET prévalence clinique faible (< 15 %)
# ─────────────────────────────────────────────────────────────────────────────

def calculer_perc(
    age_50: bool,
    fc_100: bool,
    spo2_95: bool,
    hemoptysie: bool,
    oestroprogestatif: bool,
    chirurgie_trauma_30j: bool,
    tvp_ep_atcd: bool,
    oedeme_unilateral: bool,
) -> Dict:
    """
    PERC Rule (8 critères binaires) — Exclusion EP si TOUS négatifs.
    Valide uniquement si Wells EP ≤ 1 ET prétest probability < 15 %.
    Source : Kline JA et al., J Thromb Haemost 2004.
    """
    try:
        criteres_positifs = sum([
            int(age_50), int(fc_100), int(spo2_95),
            int(hemoptysie), int(oestroprogestatif),
            int(chirurgie_trauma_30j), int(tvp_ep_atcd),
            int(oedeme_unilateral),
        ])

        if criteres_positifs == 0:
            return _result(0,
                "PERC NÉGATIF — EP exclue (probabilité post-test < 2 %)",
                "Pas de D-Dimères nécessaires si Wells EP ≤ 1 et prétest < 15 %",
                ["Kline JA et al., J Thromb Haemost 2004",
                 "Courtney DM et al., Ann Emerg Med 2010"])
        else:
            return _result(criteres_positifs,
                f"PERC POSITIF — {criteres_positifs} critère(s) — EP non exclue",
                "D-Dimères obligatoires — Continuer le bilan selon Wells",
                ["Kline JA et al., J Thromb Haemost 2004"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


# ─────────────────────────────────────────────────────────────────────────────
# GRACE Score — Risque hospitalier SCA
# Source : Eagle KA et al., JAMA 2004.
# Complément TIMI/HEART pour stratification pronostique
# ─────────────────────────────────────────────────────────────────────────────

def calculer_grace(
    age: float,
    fc: float,
    pas: float,
    creatinine_umol: float,
    arret_cardiaque: bool,
    deviation_st: bool,
    enzymes_positives: bool,
    killip: int,   # 1=pas IC, 2=râles, 3=OAP, 4=choc
) -> Dict:
    """
    GRACE Score simplifié (version calculatrice BCFI/AHA).
    Prédit la mortalité hospitalière et à 6 mois après SCA.
    Source : Eagle KA et al., JAMA 2004 (The GRACE Registry).
    """
    try:
        score = 0

        # Âge (points approximatifs selon grille GRACE)
        if age < 30:      score += 0
        elif age < 40:    score += 8
        elif age < 50:    score += 25
        elif age < 60:    score += 41
        elif age < 70:    score += 58
        elif age < 80:    score += 75
        elif age < 90:    score += 91
        else:             score += 100

        # FC
        if fc < 50:       score += 0
        elif fc < 70:     score += 3
        elif fc < 90:     score += 9
        elif fc < 110:    score += 15
        elif fc < 150:    score += 24
        elif fc < 200:    score += 38
        else:             score += 46

        # PAS
        if pas < 80:      score += 58
        elif pas < 100:   score += 53
        elif pas < 120:   score += 43
        elif pas < 140:   score += 34
        elif pas < 160:   score += 24
        elif pas < 200:   score += 10
        else:             score += 0

        # Créatinine (µmol/l)
        if creatinine_umol < 35:    score += 1
        elif creatinine_umol < 70:  score += 4
        elif creatinine_umol < 105: score += 7
        elif creatinine_umol < 140: score += 10
        elif creatinine_umol < 175: score += 13
        elif creatinine_umol < 350: score += 21
        elif creatinine_umol < 700: score += 28
        else:                       score += 31

        # Killip
        killip_pts = {1: 0, 2: 20, 3: 39, 4: 59}
        score += killip_pts.get(max(1, min(4, int(killip))), 0)

        # Variables binaires
        if arret_cardiaque:  score += 39
        if deviation_st:     score += 28
        if enzymes_positives:score += 14

        # Risque hospitalier (Eagle 2004 — table)
        if score < 109:
            risque = "Faible (< 1 %)"
            interp = f"GRACE {score} — Risque hospitalier faible"
            reco   = "Stratégie invasive non urgente — Coronarographie < 72h"
        elif score < 140:
            risque = "Intermédiaire (1-3 %)"
            interp = f"GRACE {score} — Risque intermédiaire"
            reco   = "Coronarographie < 24h — Anticoagulation + antiplaquettaire"
        else:
            risque = "Élevé (> 3 %)"
            interp = f"GRACE {score} — Risque élevé (mortalité hospit. {risque})"
            reco   = "Coronarographie urgente < 2h — USIC / Cardiologie IMMÉDIAT"

        return _result(score, interp, reco,
                       ["Eagle KA et al., JAMA 2004 — GRACE Registry",
                        "ESC NSTEMI Guidelines 2020"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


# ─────────────────────────────────────────────────────────────────────────────
# CIWA-Ar — Sevrage alcoolique (Clinical Institute Withdrawal Assessment)
# Source : Sullivan JT et al., Br J Addict 1989.
# ─────────────────────────────────────────────────────────────────────────────

def calculer_ciwa(
    nausees_vomissements: int,   # 0-7
    tremblements: int,            # 0-7
    sudation: int,                # 0-7
    anxiete: int,                 # 0-7
    agitation: int,               # 0-7
    troubles_tactiles: int,       # 0-7
    troubles_auditifs: int,       # 0-7
    troubles_visuels: int,        # 0-7
    cephalee: int,                # 0-7
    orientation: int,             # 0-4 (GCS-like)
) -> Dict:
    """
    CIWA-Ar (0-67) — Sévérité du syndrome de sevrage alcoolique.
    Source : Sullivan JT et al., Br J Addict 1989.
    """
    try:
        score = sum([
            nausees_vomissements, tremblements, sudation, anxiete, agitation,
            troubles_tactiles, troubles_auditifs, troubles_visuels,
            cephalee, orientation,
        ])

        if score < 8:
            interp = f"CIWA-Ar {score} — Sevrage léger"
            reco   = "Benzodiazépine si symptômes — Vitamines B1 IV — Hydratation"
        elif score < 15:
            interp = f"CIWA-Ar {score} — Sevrage modéré"
            reco   = "Benzodiazépine titrée (diazépam ou lorazépam) — Surveillance rapprochée"
        elif score < 20:
            interp = f"CIWA-Ar {score} — Sevrage sévère"
            reco   = "Benzodiazépine IV — Monitoring continu — Risque delirium tremens"
        else:
            interp = f"CIWA-Ar {score} — Delirium tremens / Convulsions imminentes"
            reco   = "SOINS INTENSIFS — Diazépam IV titré + Thiamine 500 mg IV — Appel réanimateur"

        return _result(score, interp, reco,
                       ["Sullivan JT et al., Br J Addict 1989",
                        "ISAM Guidelines 2022 — Alcohol withdrawal"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


# ─────────────────────────────────────────────────────────────────────────────
# PEWS — Pediatric Early Warning Score
# Source : Monaghan A, Paediatric Nursing 2005.
# ─────────────────────────────────────────────────────────────────────────────

def calculer_pews(
    comportement: int,   # 0=jouant/normal, 1=dormant, 2=irritable, 3=réduit, 4=inconscient
    cardiovasculaire: int,  # 0=rosé caprefill ≤2s, 1=pâle/CF>2s, 2=gris/CF≥3s, 3=gris+tachycardie±bradycardie
    respiratoire: int,   # 0=normal, 1=>10 FR/min/tachypnée, 2=>20 FR/min/tirage, 3=>30 ou apnée/gémissement
) -> Dict:
    """
    PEWS (0-9) — Dégradation pédiatrique précoce.
    Score ≥ 3 → appel médical ; ≥ 5 → urgence vitale.
    Source : Monaghan A, Paediatric Nursing 2005.
    """
    try:
        score = sum([
            max(0, min(4, int(comportement))),
            max(0, min(3, int(cardiovasculaire))),
            max(0, min(3, int(respiratoire))),
        ])
        # Points bonus
        if comportement >= 2 and cardiovasculaire >= 2:
            score += 1  # Majoration si 2 systèmes simultanément

        if score >= 5:
            interp = f"PEWS {score} — URGENCE VITALE PÉDIATRIQUE"
            reco   = "Appel médecin IMMÉDIAT — Activation équipe de réanimation pédiatrique"
        elif score >= 3:
            interp = f"PEWS {score} — Dégradation précoce — Surveillance rapprochée"
            reco   = "Appel médecin < 15 min — Réévaluation toutes les 30 min"
        elif score >= 1:
            interp = f"PEWS {score} — Risque modéré"
            reco   = "Surveillance horaire — Informer le médecin"
        else:
            interp = "PEWS 0 — Stable"
            reco   = "Surveillance standard"

        return _result(score, interp, reco,
                       ["Monaghan A, Paediatric Nursing 2005",
                        "RCP APLS 6th ed. 2016"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


# ═══════════════════════════════════════════════════════════════════════════════
# TOXICOLOGIE — Scores et outils d'évaluation des intoxications
# Développeur : Ismail Ibn-Daifa — Hainaut, Belgique
# Références :
#   - PSS : Persson HE et al., Eur J Clin Pharmacol 1998
#   - Rumack-Matthew : Rumack BH et al., Arch Intern Med 1975 (mis à jour MRCUK 2012)
#   - Toxidromes : Isbister GK et al., J Toxicol 2004
#   - Score tricycliques (Lacombe) : Boehnert MT, Lovejoy FH, NEJM 1985
#   - Physostigmine AChS : Schneir AB, J Emerg Med 2003
#   - TOXIC2 : Eyer F et al., Toxicol Lett 2009
#   - Centre Belge Anti-Poisons (CBP) : 070/245.245
# ═══════════════════════════════════════════════════════════════════════════════


# ─────────────────────────────────────────────────────────────────────────────
# PSS — Poisoning Severity Score
# Échelle universelle de sévérité des intoxications aiguës
# Source : Persson HE et al., Eur J Clin Pharmacol 1998 / EAPCCT
# ─────────────────────────────────────────────────────────────────────────────

PSS_CRITERES = {
    "Neurologique": {
        0: "Asymptomatique",
        1: "Somnolence légère, céphalée, vertiges",
        2: "GCS 9-14 / coma léger, agitation modérée",
        3: "Coma (GCS ≤ 8), convulsions, trouble respiratoire central",
        4: "Insuffisance respiratoire, arrêt cardiorespiratoire"
    },
    "Cardiovasculaire": {
        0: "Asymptomatique",
        1: "Tachycardie légère (FC 100-120) ou bradycardie légère",
        2: "Tachycardie sévère (> 150) / bradycardie (< 40) / hypotension",
        3: "Arythmie sévère / choc / trouble de conduction majeur",
        4: "Arrêt cardiorespiratoire"
    },
    "Respiratoire": {
        0: "Asymptomatique",
        1: "Irritation muqueuse, bronchospasme léger",
        2: "Bronchospasme modéré, dyspnée (SpO2 > 90 %)",
        3: "Détresse respiratoire sévère (SpO2 < 90 %)",
        4: "Insuffisance respiratoire, arrêt respiratoire"
    },
    "Digestif": {
        0: "Asymptomatique",
        1: "Nausées, vomissements, diarrhée légère",
        2: "Vomissements répétés, diarrhée sévère, douleur abdominale",
        3: "Hématémèse, rectorragie, perforation suspectée",
        4: "Défaillance viscérale"
    },
    "Hépatique/Rénal": {
        0: "Normal",
        1: "Enzymes légèrement élevées (< 2× N)",
        2: "Élévation modérée (2-10× N)",
        3: "Élévation majeure (> 10× N) / insuffisance",
        4: "Défaillance hépatique / rénale"
    },
}


def calculer_pss(
    neuro: int = 0, cardio: int = 0, respi: int = 0,
    digestif: int = 0, hepato_renal: int = 0,
) -> Dict:
    """
    PSS — Poisoning Severity Score (0-4).
    Le score final est le grade le plus élevé parmi tous les systèmes.
    Source : Persson HE et al., Eur J Clin Pharmacol 1998 — EAPCCT standardisation.
    """
    try:
        grade_max = max(int(neuro), int(cardio), int(respi),
                        int(digestif), int(hepato_renal))
        grade_max = max(0, min(4, grade_max))

        if grade_max == 0:
            interp = "PSS 0 — Asymptomatique"
            reco   = "Surveillance clinique — Appel CBP si doute (070/245.245)"
        elif grade_max == 1:
            interp = "PSS 1 — Intoxication légère"
            reco   = "Hospitalisation courte (4-6h) — Surveillance symptômes — CBP"
        elif grade_max == 2:
            interp = "PSS 2 — Intoxication modérée"
            reco   = "Hospitalisation — Monitorage continu — Avis toxicologique CBP"
        elif grade_max == 3:
            interp = "PSS 3 — Intoxication sévère"
            reco   = "Soins intensifs — Appel CBP IMMÉDIAT — Antidote si disponible"
        else:
            interp = "PSS 4 — Intoxication fatale / menaçant le pronostic vital"
            reco   = "Réanimation immédiate — CBP + réanimateur en urgence"

        return _result(grade_max, interp, reco,
                       ["Persson HE et al., Eur J Clin Pharmacol 1998",
                        "EAPCCT — European Association of Poisons Centres"])

    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


# ─────────────────────────────────────────────────────────────────────────────
# TOXIDROMES — Diagnostic syndromique
# Source : Isbister GK et al., J Toxicol 2004 / Pillay VV Comprehensive Medical Toxicology
# ─────────────────────────────────────────────────────────────────────────────

TOXIDROMES: List[Dict] = [
    {
        "nom":       "Syndrome opioïde",
        "signes":    ["Myosis (pupilles en pointe d'épingle)", "Bradypnée / apnée", "Coma", "Hypotension"],
        "molecules": "Morphine, codéine, fentanyl, héroïne, méthadone, tramadol",
        "antidote":  "Naloxone IV 0,4-2 mg (titration douce si dépendant : 0,04 mg/2 min)",
        "alerte":    "danger",
        "cbp_code":  "Opiates",
    },
    {
        "nom":       "Syndrome anticholinergique",
        "signes":    ["Mydriase", "Tachycardie", "Hyperthermie", "Peau sèche + rouge", "Rétention urinaire",
                      "Agitation / confusion / hallucinations", "Iléus"],
        "molecules": "Tricycliques, antihistaminiques, atropine, scopolamine, plantes (datura, belladone)",
        "antidote":  "Physostigmine 1-2 mg IV lent (si agitation sévère, sur avis CBP)",
        "alerte":    "warning",
        "cbp_code":  "Anticholinergic",
    },
    {
        "nom":       "Syndrome cholinergique (SLUDGE/DUMBELS)",
        "signes":    ["Myosis", "Bradycardie", "Hypersécrétion (sialorrhée, larmes, bronchorrhée)",
                      "Vomissements / diarrhée", "Contraction musculaire / fasciculations", "Hypotension"],
        "molecules": "Organophosphorés, carbamates, agents neurotoxiques (tabun, sarin), muscarine",
        "antidote":  "Atropine 2-4 mg IV (répéter jusqu'à assèchement sécrétions) + Pralidoxime si OP",
        "alerte":    "danger",
        "cbp_code":  "Cholinergic",
    },
    {
        "nom":       "Syndrome sympathomimétique",
        "signes":    ["Mydriase", "Tachycardie", "HTA", "Hyperthermie", "Agitation / psychose", "Diaphorèse"],
        "molecules": "Cocaïne, amphétamines, MDMA, méthylphénidate, éphédrine, pseudo-éphédrine",
        "antidote":  "Benzodiazépines (diazépam ou lorazépam IV) — Pas de bêtabloquants seuls",
        "alerte":    "warning",
        "cbp_code":  "Sympathomimetic",
    },
    {
        "nom":       "Syndrome sérotoninergique",
        "signes":    ["Triade : agitation + hyperréflexie + hyperthermie",
                      "Clonus (cheville, spontané)", "Mydriase", "Tachycardie", "Diaphorèse"],
        "molecules": "ISRS + tramadol / IMAO / linézolide / triptans / lithium (association)",
        "antidote":  "Cyproheptadine 12 mg PO + BZD — Sédation si sévère — Refroidissement si T° > 41°C",
        "alerte":    "danger",
        "cbp_code":  "Serotonin",
    },
    {
        "nom":       "Syndrome sédatif / hypnotique",
        "signes":    ["Somnolence → coma", "Hypotonie", "Nystagmus", "Ataxie",
                      "Bradypnée", "Hypothermie"],
        "molecules": "Benzodiazépines, barbituriques, GHB, alcool, zolpidem",
        "antidote":  "BZD : Flumazénil 0,2 mg IV (max 1 mg) — Attention : CI si épilepsie/dépendance",
        "alerte":    "warning",
        "cbp_code":  "Sedative",
    },
    {
        "nom":       "Syndrome cardiovasculaire (toxiques cardiaques)",
        "signes":    ["Bradycardie / bloc AV", "QRS élargi > 120 ms", "QTc allongé",
                      "Hypotension réfractaire", "Tachycardie ventriculaire"],
        "molecules": "Tricycliques, digitaliques, bêtabloquants, anticalciques, quinine, flécaïnide",
        "antidote":  "Bicarbonate 8,4 % 50-100 ml IV si QRS > 120 ms (tricycliques) | Glucagon (BB) | Intralipid® 20 % (toxiques lipophiles)",
        "alerte":    "danger",
        "cbp_code":  "Cardiac",
    },
]


def identifier_toxidrome(signes_coches: List[str]) -> List[Dict]:
    """
    Identifie les toxidromes compatibles selon les signes cochés.
    Retourne la liste triée par nombre de signes concordants.
    Source : Isbister GK et al., J Toxicol 2004.
    """
    _signes_norm = {s.lower() for s in signes_coches}
    resultats = []
    for t in TOXIDROMES:
        _signes_t = {s.lower() for s in t["signes"]}
        # Correspondances partielles (recherche par mots-clés)
        concordants = []
        for s_coche in _signes_norm:
            for s_tox in t["signes"]:
                if any(mot in s_tox.lower() for mot in s_coche.split()):
                    concordants.append(s_tox)
                    break
        if concordants:
            resultats.append({**t, "_score": len(concordants), "_concordants": concordants})
    resultats.sort(key=lambda x: x["_score"], reverse=True)
    return resultats


# ─────────────────────────────────────────────────────────────────────────────
# RUMACK-MATTHEW — Paracétamol (Acétaminophène)
# Nomogramme décisionnel pour la N-acétylcystéine (NAC)
# Source : Rumack BH et al., Arch Intern Med 1975 / MRCUK 2012 / BCFI
# ─────────────────────────────────────────────────────────────────────────────

def evaluer_paracetamol_intox(
    dose_mg_kg: Optional[float] = None,
    heure_ingestion: Optional[float] = None,
    paracetamol_serique_mgL: Optional[float] = None,
    atcd_alcool: bool = False,
    atcd_hepatique: bool = False,
    atcd_jeune: bool = False,
    medicaments_inducteurs: bool = False,
) -> Dict:
    """
    Évaluation de l'intoxication au paracétamol selon le nomogramme Rumack-Matthew.

    ZONES du nomogramme (ligne de traitement à 150 µg/ml à 4h) :
      - Au-dessus ligne 150 : NAC INDIQUÉE
      - En dessous ligne 150 : NAC non indiquée (sauf terrain à risque)
      - Terrain à risque → ligne à 100 µg/ml (seuil abaissé)

    Source : Rumack BH, Arch Intern Med 1975 — Mise à jour MRCUK 2012 — BCFI Belgique.
    """
    try:
        risk_factors = []
        if atcd_alcool:        risk_factors.append("Alcoolisme chronique (GSH abaissé)")
        if atcd_hepatique:     risk_factors.append("Hépatopathie (réserves GSH réduites)")
        if atcd_jeune:         risk_factors.append("Jeûne / dénutrition (GSH épuisé)")
        if medicaments_inducteurs: risk_factors.append("Inducteurs enzymatiques (CYP2E1) — seuil abaissé")
        terrain_risque = len(risk_factors) > 0

        details = []
        nac_indiquee = False
        urgence = False

        # ── Évaluation par dose estimée ─────────────────────────────────────
        if dose_mg_kg is not None:
            if dose_mg_kg < 75:
                details.append(f"Dose {dose_mg_kg:.0f} mg/kg < 75 mg/kg : intoxication peu probable")
            elif dose_mg_kg < 150:
                details.append(f"Dose {dose_mg_kg:.0f} mg/kg — Zone intermédiaire : dosage sérique requis")
                if terrain_risque:
                    nac_indiquee = True
                    details.append("Terrain à risque → NAC envisageable sans attendre le dosage")
            else:
                nac_indiquee = True
                urgence = True
                details.append(f"Dose {dose_mg_kg:.0f} mg/kg ≥ 150 mg/kg — NAC à initier SANS ATTENDRE le dosage")

        # ── Évaluation par paracétamolémie + heure ──────────────────────────
        if paracetamol_serique_mgL is not None and heure_ingestion is not None:
            h = float(heure_ingestion)
            c = float(paracetamol_serique_mgL)

            if h < 4:
                details.append(f"Dosage à {h:.1f}h — TROP TÔT pour le nomogramme (interpréter avec précaution)")
            elif h > 24:
                details.append(f"Dosage à {h:.1f}h — Hors nomogramme (> 24h) — Avis hépatologique urgent si bili/TP anormaux")
                urgence = True
            else:
                # Interpolation linéaire sur la ligne de traitement (Rumack-Matthew)
                # Ligne standard : 150 µg/ml à 4h → 35 µg/ml à 12h → 5 µg/ml à 24h
                # Formule: seuil = 150 × exp(-0.26 × (h - 4))
                import math
                seuil_std   = 150 * math.exp(-0.26 * (h - 4))
                seuil_risque = 100 * math.exp(-0.26 * (h - 4))  # seuil abaissé terrain à risque

                seuil_applicable = seuil_risque if terrain_risque else seuil_std

                details.append(f"Paracétamolémie {c:.0f} µg/ml à {h:.1f}h")
                details.append(f"Seuil NAC {'(terrain à risque)' if terrain_risque else '(standard)'} : {seuil_applicable:.0f} µg/ml")

                if c >= seuil_std:
                    nac_indiquee = True
                    urgence = True
                    details.append("▶ AU-DESSUS de la ligne standard → NAC INDIQUÉE")
                elif terrain_risque and c >= seuil_risque:
                    nac_indiquee = True
                    details.append("▶ Au-dessus de la ligne à risque → NAC INDIQUÉE (terrain)")
                else:
                    details.append("▶ En dessous de la ligne de traitement → NAC probablement non indiquée")

        # ── Conclusion ───────────────────────────────────────────────────────
        if nac_indiquee:
            if urgence:
                interp = "INTOXICATION AU PARACÉTAMOL — NAC URGENTE"
                reco = (
                    "N-Acétylcystéine IV (Fluimucil® Antidot) :\n"
                    "  1) 150 mg/kg dans 200 ml G5 % en 1h\n"
                    "  2) 50 mg/kg dans 500 ml G5 % en 4h\n"
                    "  3) 100 mg/kg dans 1000 ml G5 % en 16h\n"
                    "Appel CBP 070/245.245 + Avis hépatologue si > 24h"
                )
            else:
                interp = "NAC à discuter selon évolution clinique"
                reco = "Appel CBP 070/245.245 — Dosage sérique si non fait — Bilans hépatiques"
        else:
            interp = "NAC probablement non indiquée selon les données disponibles"
            reco = "Surveillance 4-6h — Bilan hépatique à 4h et 24h — CBP si doute"

        citations = [
            "Rumack BH et al., Arch Intern Med 1975",
            "Mour Revue MRCUK 2012 — Paracetamol overdose",
            "BCFI Belgique — N-Acétylcystéine (Fluimucil® Antidot)",
        ]
        return _result(
            int(nac_indiquee),
            interp,
            reco + ("\n\nFacteurs de risque : " + " | ".join(risk_factors) if risk_factors else ""),
            citations,
        ) | {"details": details, "nac_indiquee": nac_indiquee, "terrain_risque": terrain_risque}

    except (TypeError, ValueError) as e:
        return _result(None, "Données insuffisantes", f"Vérifier les paramètres ({e})", [])


# ─────────────────────────────────────────────────────────────────────────────
# SCORE TRICYCLIQUES — Critères ECG de gravité (Boehnert-Lovejoy 1985)
# QRS > 100 ms = marqueur de risque de convulsions et d'arythmies
# Source : Boehnert MT, Lovejoy FH, NEJM 1985 / Kerr GW et al., Emerg Med J 2001
# ─────────────────────────────────────────────────────────────────────────────

def evaluer_tricycliques_ecg(
    qrs_ms: float,            # Durée QRS en ms
    qtc_ms: float = 440,      # QTc en ms
    r_avr_mv: float = 0.0,    # Amplitude onde R en aVR (mV)
    rap_s_avr: float = 0.0,   # Rapport R/S en aVR
    branche_droite: bool = False,  # BBD ou empâtement S1Q3T3
) -> Dict:
    """
    Critères ECG de gravité des intoxications aux antidépresseurs tricycliques (ADT).

    Marqueurs ECG de gravité (valeur prédictive arythmies/convulsions) :
      QRS ≥ 100 ms → risque convulsions (Se 79 %)
      QRS ≥ 160 ms → risque arythmies ventriculaires (VT/FV)
      R en aVR ≥ 3 mm → spécifique intox ADT
      Rapport R/S > 0.7 en aVR → marqueur indépendant

    Source : Boehnert MT, Lovejoy FH, NEJM 1985.
    """
    try:
        score = 0
        criteres_ecg = []
        urgence_bicarbonate = False

        if qrs_ms >= 160:
            score += 3
            criteres_ecg.append(f"QRS {qrs_ms:.0f} ms ≥ 160 ms — Risque FV/TV majeur")
            urgence_bicarbonate = True
        elif qrs_ms >= 100:
            score += 2
            criteres_ecg.append(f"QRS {qrs_ms:.0f} ms ≥ 100 ms — Risque convulsions + arythmies")
            urgence_bicarbonate = True
        elif qrs_ms >= 80:
            score += 1
            criteres_ecg.append(f"QRS {qrs_ms:.0f} ms 80-99 ms — Surveillance rapprochée")

        if qtc_ms > 500:
            score += 2
            criteres_ecg.append(f"QTc {qtc_ms:.0f} ms > 500 ms — Risque torsades de pointes")
        elif qtc_ms > 440:
            score += 1
            criteres_ecg.append(f"QTc {qtc_ms:.0f} ms allongé")

        if r_avr_mv >= 3.0:
            score += 2
            criteres_ecg.append(f"R en aVR {r_avr_mv:.1f} mm ≥ 3 mm — Marqueur ADT spécifique")
        elif r_avr_mv >= 1.5:
            score += 1
            criteres_ecg.append(f"R en aVR {r_avr_mv:.1f} mm (seuil bas)")

        if rap_s_avr > 0.7:
            score += 1
            criteres_ecg.append(f"Rapport R/S aVR {rap_s_avr:.2f} > 0.7")

        if branche_droite:
            score += 1
            criteres_ecg.append("BBD ou morphologie S1Q3T3 — Effet stabilisant membranaire")

        # Classification
        if score >= 5 or qrs_ms >= 160:
            interp = f"INTOX ADT SÉVÈRE (score ECG {score}) — Arythmie imminente"
            reco = (
                "Bicarbonate NaHCO3 8,4 % : 1-2 mmol/kg IV bolus — Cible pH 7,50-7,55\n"
                "Intubation à anticiper si GCS ≤ 12\n"
                "Monitoring ECG continu — Défibrillateur prêt\n"
                "Éviter : flumazénil, physostigmine, antiarythmiques classe Ia-Ic\n"
                "CBP 070/245.245 — Réanimation"
            )
        elif score >= 2 or urgence_bicarbonate:
            interp = f"INTOX ADT MODÉRÉE (score ECG {score}) — Risque arythmie"
            reco = (
                "Envisager bicarbonate NaHCO3 si QRS ≥ 100 ms\n"
                "Monitoring ECG continu 12-24h\n"
                "Appel CBP 070/245.245 — Surveillance USI"
            )
        elif score >= 1:
            interp = f"Anomalies ECG mineures (score {score}) — Surveillance"
            reco = "ECG répété à 4h et 12h — Surveillance en salle de déchocage — CBP"
        else:
            interp = "ECG normal — Intoxication ADT moins probable ou précoce"
            reco = "ECG répété à 2h — Surveillance clinique 6h — CBP si ingestion confirmée"

        return (_result(score, interp, reco,
                        ["Boehnert MT, Lovejoy FH, NEJM 1985",
                         "Kerr GW et al., Emerg Med J 2001"])
                | {"criteres_ecg": criteres_ecg, "bicarbonate_urgent": urgence_bicarbonate})

    except (TypeError, ValueError) as e:
        return _result(None, "Données insuffisantes", f"Vérifier les paramètres ({e})", [])


# ─────────────────────────────────────────────────────────────────────────────
# SCORE TOXIC2 — Indication d'hospitalisation / transfert USI
# Intoxications médicamenteuses aiguës — Score de triage
# Source : Eyer F et al., Clin Toxicol 2009 / adapté pratique Hainaut
# ─────────────────────────────────────────────────────────────────────────────

def calculer_toxic2(
    gcs: int = 15,
    fc_anormale: bool = False,     # FC < 50 ou > 130 bpm
    pas_basse: bool = False,       # PAS < 90 mmHg
    spo2_basse: bool = False,      # SpO2 < 92 %
    qrs_large: bool = False,       # QRS ≥ 120 ms
    qtc_long: bool = False,        # QTc > 500 ms
    molecule_cardiotoxique: bool = False,  # Tricycliques, digitaliques, antiarythmiques
    tentative_suicide: bool = False,
    intox_multiple: bool = False,
) -> Dict:
    """
    TOXIC2 — Score d'aide à la décision de niveau de soins.
    Score ≥ 2 → hospitalisation USI/USIC recommandée.
    Source : Eyer F et al., Clin Toxicol 2009.
    """
    try:
        score = 0
        items = []

        # Critères neurologiques
        if gcs <= 8:
            score += 3; items.append(f"GCS {gcs} ≤ 8 — Coma")
        elif gcs <= 12:
            score += 2; items.append(f"GCS {gcs} 9-12 — Altération modérée")
        elif gcs < 15:
            score += 1; items.append(f"GCS {gcs} 13-14")

        # Critères cardiovasculaires
        if fc_anormale:  score += 2; items.append("FC < 50 ou > 130 bpm")
        if pas_basse:    score += 2; items.append("PAS < 90 mmHg")
        if qrs_large:    score += 2; items.append("QRS ≥ 120 ms")
        if qtc_long:     score += 1; items.append("QTc > 500 ms")

        # Critères respiratoires
        if spo2_basse:   score += 2; items.append("SpO2 < 92 %")

        # Contexte
        if molecule_cardiotoxique: score += 1; items.append("Molécule cardiotoxique")
        if intox_multiple:         score += 1; items.append("Intoxication poly-médicamenteuse")
        if tentative_suicide:      score += 1; items.append("Tentative de suicide")

        if score >= 5:
            interp = f"TOXIC2 {score} — Réanimation / USIC indiquée"
            reco   = "Transfert réanimation immédiat — Monitoring continu — Appel CBP 070/245.245"
        elif score >= 3:
            interp = f"TOXIC2 {score} — USI recommandée"
            reco   = "Hospitalisation en unité de soins intensifs — Monitoring cardiaque — CBP"
        elif score >= 1:
            interp = f"TOXIC2 {score} — Hospitalisation standard — Surveillance rapprochée"
            reco   = "Salle d'urgence ou HDJ — ECG série — Bilans biologiques — CBP si doute"
        else:
            interp = "TOXIC2 0 — Ambulatoire envisageable après observation"
            reco   = "Observation 4-6h — Évaluation psychiatrique si tentative — Appel CBP"

        return (_result(score, interp, reco,
                        ["Eyer F et al., Clin Toxicol 2009",
                         "Centre Belge Anti-Poisons — Protocole triage intox."])
                | {"items_positifs": items})

    except (TypeError, ValueError) as e:
        return _result(None, "Données insuffisantes", f"Vérifier les paramètres ({e})", [])


# ═══════════════════════════════════════════════════════════════════════════════
# NIHSS SIMPLIFIÉ — 5 items — Triage AVC rapide
# Source : Schiemanck SK et al., Cerebrovasc Dis 2006 / Pradat-Diehl P 2008
# Validé pour évaluation rapide IAO — corrélation r=0.89 avec NIHSS complet
# ═══════════════════════════════════════════════════════════════════════════════

def calculer_nihss_rapide(
    conscience: int = 0,       # 0=normal 1=somnolent 2=stuporeux 3=coma
    regard: bool = False,      # Déviation conjuguée du regard
    facial: int = 0,           # 0=normal 1=légère 2=partielle 3=complète
    moteur_bras: int = 0,      # 0=normal 1=dérive 2=contre grav. 3=aucun 4=pas de mvt
    langage: int = 0,          # 0=normal 1=aphasie légère 2=aphasie sévère 3=muet
) -> Dict:
    """
    NIHSS simplifié 5 items — Évaluation rapide AVC en IAO.
    Score 0-18 — Seuil de thrombolyse : tout score ≥ 1 + délai < 4,5h.

    Interprétation :
      0     : Pas de déficit
      1-4   : AVC mineur
      5-15  : AVC modéré → thrombolyse possible
      16-20 : AVC sévère → thrombolyse à discuter
      > 20  : AVC très sévère
    Source : Schiemanck et al., Cerebrovasc Dis 2006.
    """
    try:
        score = int(conscience) + (2 if regard else 0) + int(facial) + int(moteur_bras) + int(langage)
        score = max(0, min(18, score))

        if score == 0:
            interp = "NIHSS 0 — Pas de déficit neurologique objectivable"
            reco   = "Observation — Bilan standard AVC si symptômes récents"
        elif score <= 4:
            interp = f"NIHSS {score} — AVC mineur (MACE risque faible)"
            reco   = "TDM cérébral + angio-IRM en urgence — Filière Stroke"
        elif score <= 15:
            interp = f"NIHSS {score} — AVC modéré — Thrombolyse à évaluer"
            reco   = "Code Stroke activé — Délai ≤ 4,5h = thrombolyse — Appel neurologue IMMÉDIAT"
        elif score <= 20:
            interp = f"NIHSS {score} — AVC sévère"
            reco   = "Code Stroke — Thrombectomie à discuter — USI neurologique"
        else:
            interp = f"NIHSS {score} — AVC très sévère"
            reco   = "Soins intensifs neurologiques — Pronostic sévère"

        return _result(score, interp, reco, ["Schiemanck SK et al., Cerebrovasc Dis 2006"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


# ═══════════════════════════════════════════════════════════════════════════════
# GRACE SCORE — SCA NSTEMI/UA — Mortalité à 6 mois
# Source : Fox KAA et al., BMJ 2006 — ESC 2023 recommande GRACE ou TIMI
# ═══════════════════════════════════════════════════════════════════════════════

def calculer_grace(
    age: float,
    fc: float,
    pas: float,
    creatinine_mgdl: float = 1.0,
    killip: int = 1,         # 1=pas ICA 2=râles 3=OAP 4=choc
    arret_cardiaque: bool = False,
    ecg_sus_st: bool = False,
    troponine: bool = False,
) -> Dict:
    """
    GRACE Score — Risque décès intra-hospitalier SCA NSTEMI/UA.
    Recommandé ESC 2023 pour stratification NSTEMI.

    Score > 140 = haut risque → coronarographie < 24h
    Score 109-140 = risque intermédiaire → coronarographie < 72h
    Score < 109 = faible risque → coronarographie élective

    Source : Fox KAA et al., BMJ 2006 — doi:10.1136/bmj.38985.646481.55
    """
    try:
        score = 0

        # Âge (0-100)
        if age < 30:    score += 0
        elif age < 40:  score += 8
        elif age < 50:  score += 25
        elif age < 60:  score += 41
        elif age < 70:  score += 58
        elif age < 80:  score += 75
        else:           score += 91

        # FC (bpm)
        if fc < 50:     score += 0
        elif fc < 70:   score += 3
        elif fc < 90:   score += 9
        elif fc < 110:  score += 15
        elif fc < 150:  score += 24
        elif fc < 200:  score += 38
        else:           score += 46

        # PAS systolique (mmHg)
        if pas < 80:      score += 58
        elif pas < 100:   score += 53
        elif pas < 120:   score += 43
        elif pas < 140:   score += 34
        elif pas < 160:   score += 24
        elif pas < 200:   score += 10
        else:             score += 0

        # Créatinine → points approximatifs
        if creatinine_mgdl < 0.4:   score += 1
        elif creatinine_mgdl < 0.8: score += 4
        elif creatinine_mgdl < 1.2: score += 7
        elif creatinine_mgdl < 1.6: score += 10
        elif creatinine_mgdl < 2.0: score += 13
        elif creatinine_mgdl < 4.0: score += 21
        else:                        score += 28

        # Killip
        killip_pts = {1: 0, 2: 20, 3: 39, 4: 59}
        score += killip_pts.get(int(killip), 0)

        # Variables binaires
        if arret_cardiaque: score += 39
        if ecg_sus_st:      score += 28
        if troponine:       score += 14

        if score < 109:
            interp = f"GRACE {score} — Risque faible (mortalité hospit. < 1 %)"
            reco   = "Coronarographie élective (< 72h si stable) — Surveillance standard"
        elif score <= 140:
            interp = f"GRACE {score} — Risque intermédiaire (mortalité 1-3 %)"
            reco   = "Coronarographie dans les 24-72h — Anticoagulation + antiagrégation"
        else:
            interp = f"GRACE {score} — Risque élevé (mortalité > 3 %)"
            reco   = "Coronarographie urgente < 24h — USIC — Double antiagrégation"

        return _result(score, interp, reco, ["Fox KAA et al., BMJ 2006", "ESC 2023 — SCA NSTEMI"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


# ═══════════════════════════════════════════════════════════════════════════════
# SCORE PRAM — Asthme Pédiatrique — Sévérité en urgence
# Source : Chalut DS et al., J Pediatr 2000
# ═══════════════════════════════════════════════════════════════════════════════

def calculer_pram(
    spo2: float,
    tirage_sus_sternal: bool = False,
    tirage_sous_costal: bool = False,
    tirage_intercostal: bool = False,
    entree_air: int = 1,   # 1=normale 2=diminuée 3=très diminuée/absente
    wheezing: int = 1,     # 1=absent 2=expi. seul 3=inspi+expi 4=audible sans stetho
) -> Dict:
    """
    PRAM — Paediatric Respiratory Assessment Measure.
    Score asthme pédiatrique — 0-12 points.
    Score < 4 : léger | 4-7 : modéré | ≥ 8 : sévère
    Source : Chalut DS et al., J Pediatr 2000.
    """
    try:
        score = 0

        # SpO2
        if spo2 >= 95:   score += 0
        elif spo2 >= 92: score += 1
        elif spo2 >= 90: score += 2
        else:             score += 3

        # Tirage
        if tirage_sus_sternal:  score += 2
        if tirage_sous_costal:  score += 2
        if tirage_intercostal:  score += 1  # non inclus dans PRAM original — bonus clinique

        # Entrée d'air
        score += max(0, int(entree_air) - 1) * 1

        # Wheezing
        score += max(0, int(wheezing) - 1) * 1

        score = max(0, min(12, score))

        if score < 4:
            interp = f"PRAM {score} — Asthme léger"
            reco   = "Salbutamol inhalateur — Réévaluation à 20 min"
        elif score < 8:
            interp = f"PRAM {score} — Asthme modéré"
            reco   = "Salbutamol nébulisation (5 mg) × 3/h — SpO2 + scope — Appel médecin"
        else:
            interp = f"PRAM {score} — Asthme sévère"
            reco   = "O2 haut débit + Salbutamol + Ipratropium nébulisation — Appel pédiatre IMMÉDIAT"

        return _result(score, interp, reco, ["Chalut DS et al., J Pediatr 2000",
                                              "GINA 2023 Pédiatrique"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


# ═══════════════════════════════════════════════════════════════════════════════
# SCORES PÉDIATRIQUES SUPPLÉMENTAIRES
# ═══════════════════════════════════════════════════════════════════════════════

# ── Score de Kristjansson (croup/laryngite sous-glottique) ──────────────────
# Source : Kristjansson S et al., Acta Paediatr 1994 — Stridor / croup
def calculer_croup(stridor: int = 0, tirage: int = 0,
                   cyanose: bool = False, entree_air: int = 0,
                   conscience: int = 0) -> Dict:
    """
    Score de Westley adapté — Croup / Laryngite sous-glottique pédiatrique.
    0-2 : léger | 3-5 : modéré | ≥ 6 : sévère (hospitalisation USP)
    Source : Westley CR et al., Am J Dis Child 1978.
    """
    try:
        score = (int(stridor) + int(tirage) + int(entree_air) +
                 int(conscience) + (5 if cyanose else 0))
        score = max(0, min(17, score))
        if cyanose or score >= 6:
            interp = f"Croup sévère (score {score}) — Adrénaline nébulisée + O₂ immédiat"
            reco   = ("Adrénaline racémique 0,5 ml/kg nébulisation (max 5 ml) + "
                      "Dexaméthasone 0,6 mg/kg PO/IV + O₂ — Appel pédiatre IMMÉDIAT")
        elif score >= 3:
            interp = f"Croup modéré (score {score})"
            reco   = "Dexaméthasone 0,15-0,6 mg/kg PO — Surveillance SpO₂ — Appel pédiatre"
        else:
            interp = f"Croup léger (score {score})"
            reco   = "Dexaméthasone 0,15 mg/kg PO — Surveillance ambulatoire possible"
        return _result(score, interp, reco,
                       ["Westley CR et al., Am J Dis Child 1978"])
    except (TypeError, ValueError):
        return _result(None, "Données insuffisantes", "Vérifier les paramètres", [])


# ── Poids estimé enfant — formule APLS ─────────────────────────────────────
# Source : APLS (Advanced Paediatric Life Support) 6th ed. 2016
def poids_estime_enfant(age_ans: float) -> Optional[float]:
    """
    Formule APLS 2016 pour estimation du poids pédiatrique en urgence :
    < 1 an  : (âge_mois / 2) + 4
    1-5 ans : (2 × âge) + 8
    6-12 ans: (3 × âge) + 7
    Source : Advanced Paediatric Life Support 6th ed. 2016.
    """
    try:
        if age_ans < 0:
            return None
        elif age_ans < 1:
            mois = age_ans * 12
            return round(mois / 2 + 4, 1)
        elif age_ans <= 5:
            return round(2 * age_ans + 8, 1)
        elif age_ans <= 12:
            return round(3 * age_ans + 7, 1)
        else:
            return None   # formule non valide > 12 ans
    except (TypeError, ValueError):
        return None


# ── Surface corporelle pédiatrique (Mosteller) ─────────────────────────────
# Source : Mosteller RD, N Engl J Med 1987
def surface_corporelle_mosteller(poids_kg: float, taille_cm: float) -> Optional[float]:
    """
    Formule de Mosteller : SC (m²) = √(poids × taille / 3600).
    Utilisée pour dosage chimiothérapie et calcul débit pédiatrique.
    Source : Mosteller RD, N Engl J Med 1987.
    """
    try:
        if poids_kg <= 0 or taille_cm <= 0:
            return None
        import math
        return round(math.sqrt(poids_kg * taille_cm / 3600), 2)
    except (TypeError, ValueError):
        return None


# ── Règle de Naegele — Terme prévu ─────────────────────────────────────────
def terme_naegele(date_dernières_regles: str) -> Optional[str]:
    """
    Règle de Naegele : terme = DDR + 280 jours (40 semaines).
    Entrée : date DDR au format 'JJ/MM/AAAA' ou 'AAAA-MM-JJ'.
    Retourne terme prévu + semaines d'aménorrhée actuelles.
    Source : Naegele FC, 1812 — Standardisé obstétrique moderne.
    """
    try:
        from datetime import datetime, timedelta
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
            try:
                ddr = datetime.strptime(date_dernières_regles.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return None
        terme = ddr + timedelta(days=280)
        sa_actuelles = (datetime.now() - ddr).days // 7
        return (f"Terme : {terme.strftime('%d/%m/%Y')} — "
                f"SA actuelles : {sa_actuelles} SA")
    except Exception:
        return None
