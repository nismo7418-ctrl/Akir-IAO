# clinical/scores.py — Scores cliniques validés — AKIR-IAO v19.0
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


def calculer_timi(age_65: bool, risk_factors: bool, coronaropathie: bool, ecg: bool, angine_severe: bool, aspirine: bool, marqueurs: bool) -> Dict:
    """TIMI NSTEMI. Source: Antman EM et al., JAMA 2000."""
    try:
        score = sum([int(age_65), int(risk_factors), int(coronaropathie), int(ecg), int(angine_severe), int(aspirine), int(marqueurs)])
        if score <= 2:
            return _result(score, f"TIMI {score} — Risque faible", "Traitement médical conservateur", ["Antman EM et al., JAMA 2000"])
        elif score <= 4:
            return _result(score, f"TIMI {score} — Risque intermédiaire", "Coronarographie dans les 24-48h", ["Antman EM et al., JAMA 2000"])
        return _result(score, f"TIMI {score} — Risque élevé", "Coronarographie urgente < 24h", ["Antman EM et al., JAMA 2000"])
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
