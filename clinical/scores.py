from typing import List, Optional, Tuple


def calculer_gcs(y: int, v: int, m: int) -> Tuple[int, List[str]]:
    try:
        return max(3, min(15, int(y) + int(v) + int(m))), []
    except Exception:
        return 15, ["Erreur GCS"]


def calculer_qsofa(
    fr: Optional[float],
    gcs: Optional[int],
    pas: Optional[float],
) -> Tuple[int, List[str], List[str]]:
    s = 0
    pos: List[str] = []
    w: List[str] = []
    if fr is None:
        w.append("FR manquante")
    elif fr >= 22:
        s += 1
        pos.append(f"FR {fr}/min")
    if gcs is None:
        w.append("GCS manquant")
    elif gcs < 15:
        s += 1
        pos.append(f"GCS {gcs}/15")
    if pas is None:
        w.append("PAS manquante")
    elif pas <= 100:
        s += 1
        pos.append(f"PAS {pas} mmHg")
    return s, pos, w


def calculer_timi(
    age: float,
    nb_frcv: int,
    sten: bool,
    aspi: bool,
    trop: bool,
    dst: bool,
    cris: int,
) -> Tuple[int, List[str]]:
    try:
        s = (
            int(age >= 65)
            + int(nb_frcv >= 3)
            + int(bool(sten))
            + int(bool(aspi))
            + int(bool(trop))
            + int(bool(dst))
            + int(cris >= 2)
        )
        return s, []
    except Exception as e:
        return 0, [str(e)]


def evaluer_fast(f: bool, a: bool, s: bool, t: bool) -> Tuple[int, str, bool]:
    sc = int(bool(f)) + int(bool(a)) + int(bool(s)) + int(bool(t))
    if sc >= 2:
        return sc, "FAST positif - AVC probable - Filiere Stroke", True
    if sc == 1:
        return sc, "FAST partiel - Evaluation urgente", False
    return sc, "FAST negatif", False


def calculer_algoplus(
    v: bool,
    r: bool,
    p: bool,
    ac: bool,
    co: bool,
) -> Tuple[int, str, str, List[str]]:
    try:
        sc = int(bool(v)) + int(bool(r)) + int(bool(p)) + int(bool(ac)) + int(bool(co))
        if sc >= 4:
            return sc, "Douleur intense - traitement IV urgent", "danger", []
        if sc >= 2:
            return sc, "Douleur probable - traitement a initier", "warning", []
        return sc, "Douleur absente ou peu probable", "success", []
    except Exception as e:
        return 0, "Erreur", "info", [str(e)]


def evaluer_cfs(sc: int) -> Tuple[str, str, bool]:
    if sc <= 3:
        return "Robuste", "success", False
    if sc <= 4:
        return "Vulnerable", "warning", False
    if sc <= 6:
        return "Fragile", "warning", True
    if sc <= 8:
        return "Tres fragile", "danger", True
    return "Terminal", "danger", True


def calculer_heart(hist: int, ecg: int, age: int, risk: int, trop: int) -> Tuple[int, str, str]:
    score = int(hist) + int(ecg) + int(age) + int(risk) + int(trop)
    if score <= 3:
        return score, "Risque faible - sortie ou observation courte", "success"
    if score <= 6:
        return score, "Risque intermediaire - bilan et surveillance", "warning"
    return score, "Risque eleve - syndrome coronarien a considerer", "danger"


def calculer_wells_tvp(*items) -> Tuple[int, str, str]:
    score = sum(int(bool(x)) for x in items)
    if score >= 3:
        return score, "Probabilite clinique elevee de TVP", "danger"
    if score >= 1:
        return score, "Probabilite intermediaire de TVP", "warning"
    return score, "Probabilite faible de TVP", "success"


def calculer_wells_ep(*items) -> Tuple[int, str, str]:
    score = sum(int(bool(x)) for x in items)
    if score >= 7:
        return score, "Probabilite elevee d'embolie pulmonaire", "danger"
    if score >= 3:
        return score, "Probabilite intermediaire d'embolie pulmonaire", "warning"
    return score, "Probabilite faible d'embolie pulmonaire", "success"


def calculer_nihss(*items) -> Tuple[int, str, str]:
    score = sum(int(x or 0) for x in items)
    if score <= 4:
        return score, "AVC mineur", "success"
    if score <= 15:
        return score, "AVC modere", "warning"
    if score <= 24:
        return score, "AVC severe", "danger"
    return score, "AVC tres severe", "danger"


def calculer_sofa_partiel(
    pas: float,
    gcs: int,
    vaso: bool,
    pao_fio2: Optional[float] = None,
    plaq: Optional[float] = None,
    creat: Optional[float] = None,
) -> Tuple[int, List[str]]:
    score = 0
    notes: List[str] = []

    if pao_fio2 is not None:
        if pao_fio2 < 100:
            score += 4
        elif pao_fio2 < 200:
            score += 3
        elif pao_fio2 < 300:
            score += 2
        elif pao_fio2 < 400:
            score += 1
        notes.append(f"Respiratoire: PaO2/FiO2 {pao_fio2}")
    else:
        notes.append("Respiratoire non renseigne")

    if plaq is not None:
        if plaq < 20:
            score += 4
        elif plaq < 50:
            score += 3
        elif plaq < 100:
            score += 2
        elif plaq < 150:
            score += 1
        notes.append(f"Plaquettes: {plaq} x10^3/uL")
    else:
        notes.append("Plaquettes non renseignees")

    if gcs < 6:
        score += 4
    elif gcs < 10:
        score += 3
    elif gcs < 13:
        score += 2
    elif gcs < 15:
        score += 1
    notes.append(f"Neurologique: GCS {gcs}")

    if vaso:
        score += 3
        notes.append("Hemodynamique: vasopresseurs")
    elif pas < 70:
        score += 2
        notes.append(f"Hemodynamique: hypotension severe PAS {pas}")
    elif pas < 90:
        score += 1
        notes.append(f"Hemodynamique: hypotension PAS {pas}")

    if creat is not None:
        if creat >= 440:
            score += 4
        elif creat >= 300:
            score += 3
        elif creat >= 171:
            score += 2
        elif creat >= 110:
            score += 1
        notes.append(f"Renal: creatinine {creat} umol/L")
    else:
        notes.append("Creatinine non renseignee")

    return score, notes


def calculer_curb65(confusion: bool, uree: bool, fr30: bool, pas90: bool, age65: bool) -> Tuple[int, str, str]:
    score = sum(int(bool(x)) for x in (confusion, uree, fr30, pas90, age65))
    if score <= 1:
        return score, "Faible risque - traitement ambulatoire possible", "success"
    if score == 2:
        return score, "Risque intermediaire - hospitalisation a discuter", "warning"
    return score, "Risque eleve - hospitalisation / soins aigus", "danger"


def regle_ottawa_cheville(
    pas_appui: bool,
    mall_med: bool,
    mall_lat: bool,
    base_5e: bool,
    naviculaire: bool,
) -> Tuple[bool, str, str]:
    positif = any((pas_appui, mall_med, mall_lat, base_5e, naviculaire))
    if positif:
        return True, "Radiographie cheville / pied indiquee", "warning"
    return False, "Pas de radiographie selon Ottawa", "success"


def regle_canadian_ct(
    gcs_2h: bool,
    fract_ouverte: bool,
    vom2: bool,
    age65: bool,
    amnesie30: bool,
    mecanisme_dangereux: bool,
) -> Tuple[bool, str, str]:
    haut_risque = any((gcs_2h, fract_ouverte, vom2, age65))
    moyen_risque = any((amnesie30, mecanisme_dangereux))
    if haut_risque:
        return True, "TDM cerebrale indiquee - haut risque", "danger"
    if moyen_risque:
        return True, "TDM cerebrale a considerer - risque intermediaire", "warning"
    return False, "Pas d'indication immediate selon la regle canadienne", "success"
