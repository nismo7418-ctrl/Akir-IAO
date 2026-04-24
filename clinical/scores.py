from typing import Optional, List, Tuple

def calculer_gcs(y: int, v: int, m: int) -> Tuple[int, List[str]]:
    try: return max(3, min(15, int(y)+int(v)+int(m))), []
    except: return 15, ["Erreur GCS"]

def calculer_qsofa(fr: Optional[float], gcs: Optional[int],
                   pas: Optional[float]) -> Tuple[int, List[str], List[str]]:
    s = 0; pos = []; w = []
    if fr is None: w.append("FR manquante")
    elif fr >= 22: s += 1; pos.append(f"FR {fr}/min")
    if gcs is None: w.append("GCS manquant")
    elif gcs < 15: s += 1; pos.append(f"GCS {gcs}/15")
    if pas is None: w.append("PAS manquante")
    elif pas <= 100: s += 1; pos.append(f"PAS {pas}mmHg")
    return s, pos, w

def calculer_timi(age: float, nb_frcv: int, sten: bool,
                  aspi: bool, trop: bool, dst: bool,
                  cris: int) -> Tuple[int, List[str]]:
    try:
        s = (int(age>=65) + int(nb_frcv>=3) + int(bool(sten)) + int(bool(aspi))
             + int(bool(trop)) + int(bool(dst)) + int(cris>=2))
        return s, []
    except Exception as e: return 0, [str(e)]

def evaluer_fast(f: bool, a: bool, s: bool, t: bool) -> Tuple[int, str, bool]:
    sc = int(bool(f)) + int(bool(a)) + int(bool(s)) + int(bool(t))
    if sc >= 2: return sc, "FAST positif — AVC probable — Filière Stroke", True
    if sc == 1: return sc, "FAST partiel — Évaluation urgente", False
    return sc, "FAST négatif", False

def calculer_algoplus(v: bool, r: bool, p: bool,
                      ac: bool, co: bool) -> Tuple[int, str, str, List[str]]:
    try:
        sc = int(bool(v)) + int(bool(r)) + int(bool(p)) + int(bool(ac)) + int(bool(co))
        if sc >= 4: return sc, "Douleur intense — traitement IV urgent", "danger", []
        elif sc >= 2: return sc, "Douleur probable — traitement à initier", "warning", []
        return sc, "Douleur absente ou peu probable", "success", []
    except Exception as e: return 0, "Erreur", "info", [str(e)]

def evaluer_cfs(sc: int) -> Tuple[str, str, bool]:
    if sc <= 3: return "Robuste", "success", False
    if sc <= 4: return "Vulnérable", "warning", False
    if sc <= 6: return "Fragile", "warning", True
    if sc <= 8: return "Très fragile", "danger", True
    return "Terminal", "danger", True
