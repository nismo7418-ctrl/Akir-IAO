"""
clinical/prefill.py — Helpers de pré-remplissage inter-modules.

Évite à l'IAO de re-saisir les mêmes données dans les modules ML (IA Triage,
Mortalité ICU, Réadmission J30). Pures functions, sans dépendance Streamlit.

Fonctions publiques :
    gcs_to_avpu(gcs)           → str ("A","V","P","U")
    atcd_to_charlson(atcd)     → list[str] (clés Charlson)
    motif_is_trauma(motif)     → bool
    build_triage_payload(ss)   → dict prêt pour ml.triage_predictor
    build_mortality_payload(ss)→ dict prêt pour ml.mortality_predictor
    build_readmission_prefill(ss) → dict {urgence, comorbidites, ...}
"""
from __future__ import annotations

from typing import Iterable


# ──────────────────────────────────────────────────────────────────────────────
# Mapping ATCD (config.py) → comorbidités Charlson (readmission_tab._COMORBIDITES_OPTIONS)
# Clés Charlson correspondent à ml.readmission_predictor + clinical.scores.calculer_lace
# ──────────────────────────────────────────────────────────────────────────────

_ATCD_TO_CHARLSON: dict[str, list[str]] = {
    "Coronaropathie / SCA antérieur": ["infarctus"],
    "Insuffisance cardiaque":         ["insuffisance_cardiaque"],
    "AVC / AIT antérieur":            ["avc"],
    "Démence":                        ["demence"],
    "BPCO":                           ["bpco"],
    "Asthme":                         ["bpco"],  # asthme sévère regroupé avec BPCO dans Charlson
    "Ulcère gastro-duodénal":         ["ulcere_peptique"],
    "Diabète type 1":                 ["diabete_sans_compl"],
    "Diabète type 2":                 ["diabete_sans_compl"],
    "Insuffisance hépatique":         ["maladie_hepatique_legere"],
    "Insuffisance rénale chronique":  ["irc_moderee"],
    "Chimiothérapie en cours":        ["tumeur_solide"],
    "Immunodépression":               ["sida"],
}


def atcd_to_charlson(atcd: Iterable[str] | None) -> list[str]:
    """Convertit une liste d'ATCD (libellés français AKIR) en clés Charlson.

    Doublons éliminés, ordre stable (ordre d'apparition dans atcd).
    """
    if not atcd:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for label in atcd:
        for key in _ATCD_TO_CHARLSON.get(str(label).strip(), []):
            if key not in seen:
                seen.add(key)
                out.append(key)
    return out


def atcd_contains_anticoag(atcd: Iterable[str] | None) -> bool:
    """True si la liste d'ATCD contient un anticoagulant ou AVK."""
    if not atcd:
        return False
    norm = " ".join(str(a).lower() for a in atcd)
    return any(k in norm for k in (
        "anticoagulant", "aod", "avk", "eliquis", "xarelto", "pradaxa",
        "lixiana", "sintrom", "warfarine", "coumadine",
    ))


# ──────────────────────────────────────────────────────────────────────────────
# Mapping GCS → AVPU (pour le modèle triage v2)
# Source : Kelly CA et al., Resuscitation 2004 — équivalence cliniquement admise.
# ──────────────────────────────────────────────────────────────────────────────

def gcs_to_avpu(gcs: int | None) -> str:
    """Convertit un GCS (3-15) en lettre AVPU.

    Mapping (Kelly 2004) :
        GCS 15      → "A" (Alert)
        GCS 13-14   → "V" (Voice — répond à la voix)
        GCS 9-12    → "P" (Pain — répond à la douleur)
        GCS ≤ 8     → "U" (Unresponsive)
    """
    if gcs is None:
        return "A"
    try:
        g = int(gcs)
    except (TypeError, ValueError):
        return "A"
    if g >= 15:
        return "A"
    if g >= 13:
        return "V"
    if g >= 9:
        return "P"
    return "U"


# ──────────────────────────────────────────────────────────────────────────────
# Détection trauma depuis motif libre
# ──────────────────────────────────────────────────────────────────────────────

_TRAUMA_KEYWORDS = (
    "trauma", "traumat", "chute", "accident", "fracture", "plaie",
    "brûlure", "brulure", "polytrauma", "ecrasement", "écrasement",
    "agression", "morsure", "blessure",
)


def motif_is_trauma(motif: str | None) -> bool:
    """True si le motif décrit un traumatisme."""
    if not motif:
        return False
    return any(k in str(motif).lower() for k in _TRAUMA_KEYWORDS)


def motif_is_avc_suspect(motif: str | None) -> bool:
    """True si le motif évoque un AVC / déficit neurologique."""
    if not motif:
        return False
    return any(k in str(motif).lower() for k in (
        "avc", "déficit", "deficit", "hémiplégie", "hemiplegie",
        "aphasie", "stroke", "be-fast", "fast",
    ))


# ──────────────────────────────────────────────────────────────────────────────
# Builders de payload pour les 3 modules ML
# `ss` = streamlit session_state (passé en argument pour rester pure)
# ──────────────────────────────────────────────────────────────────────────────

def _sget(ss, key: str, default=None):
    """Helper compatible session_state ET dict (pour les tests)."""
    if hasattr(ss, "get"):
        return ss.get(key, default)
    return getattr(ss, key, default)


def build_triage_payload(ss, *, ambulance: bool = False) -> dict:
    """Construit le dict prêt pour ml.triage_predictor.get_ml_priority().

    Utilise les vitaux courants saisis dans l'onglet Triage + dérive AVPU
    depuis le GCS et le flag 'injury' depuis le motif.
    """
    fc   = float(_sget(ss, "v_fc", 80))
    pas  = float(_sget(ss, "v_pas", 120))
    pad  = float(_sget(ss, "v_pad", pas * 0.65))
    return {
        "fc":   fc,
        "fr":   float(_sget(ss, "v_fr", 16)),
        "pas":  pas,
        "pad":  pad,
        "spo2": float(_sget(ss, "v_spo2", 98)),
        "temp": float(_sget(ss, "v_temp", 37.0)),
        "avpu": gcs_to_avpu(_sget(ss, "v_gcs", 15)),
        "nrs_pain":          int(_sget(ss, "eva", 0) or 0),
        "arrival_ambulance": int(bool(ambulance)),
        "injury":            int(motif_is_trauma(_sget(ss, "motif", ""))),
    }


def build_mortality_payload(ss) -> dict:
    """Construit le dict prêt pour ml.mortality_predictor.predict_mortality().

    Calcule les agrégats (mean/min/max) à partir des vitaux courants + de
    l'historique des réévaluations si dispo. Si pas de réévaluations,
    utilise des bornes ±15 % autour de la valeur courante (cohérent avec
    les variations physiologiques en USI).
    """
    fc   = float(_sget(ss, "v_fc", 88))
    pas  = float(_sget(ss, "v_pas", 115))
    spo2 = float(_sget(ss, "v_spo2", 96))
    fr   = float(_sget(ss, "v_fr", 18))
    temp = float(_sget(ss, "v_temp", 37.0))
    pad  = float(_sget(ss, "v_pad", pas * 0.65))

    reevs = _sget(ss, "reevs", []) or []

    def _series(key: str, fallback: float) -> list[float]:
        """Construit la série temporelle à partir des réévaluations + valeur courante."""
        vals = [fallback]
        for r in reevs:
            v = r.get(key) if isinstance(r, dict) else None
            if v is not None:
                try:
                    vals.append(float(v))
                except (TypeError, ValueError):
                    pass
        return vals

    fc_s   = _series("fc",   fc)
    pas_s  = _series("pas",  pas)
    spo2_s = _series("spo2", spo2)
    fr_s   = _series("fr",   fr)
    temp_s = _series("temp", temp)

    def _agg(series: list[float], var: float = 0.10) -> tuple[float, float, float]:
        """Retourne (mean, min, max). Si série courte, étend min/max par ±var %."""
        if len(series) >= 3:
            return (sum(series) / len(series), min(series), max(series))
        m = sum(series) / len(series)
        return (m, m * (1 - var), m * (1 + var))

    fc_m,   fc_min,   fc_max   = _agg(fc_s,   0.15)
    pas_m,  pas_min,  _        = _agg(pas_s,  0.12)
    spo2_m, spo2_min, _        = _agg(spo2_s, 0.05)
    _,      _,        rr_max   = _agg(fr_s,   0.15)
    temp_m, _,        temp_max = _agg(temp_s, 0.02)
    fr_m    = sum(fr_s) / len(fr_s)
    map_m   = (pas_m + 2 * pad) / 3
    map_min = (pas_min + 2 * pad) / 3

    return {
        "hr_mean":          fc_m,    "hr_min": fc_min,     "hr_max": fc_max,
        "spo2_mean":        spo2_m,  "spo2_min": spo2_min,
        "rr_mean":          fr_m,    "rr_max": rr_max,
        "sbp_mean":         pas_m,   "sbp_min": pas_min,
        "dbp_mean":         pad,
        "map_mean":         map_m,   "map_min": map_min,
        "temp_c_mean":      temp_m,  "temp_c_max": temp_max,
        "shock_index":      fc_m / pas_m if pas_m > 0 else 1.0,
        "los_hours":        _sget(ss, "los_hours", 24),
        "admission_type_enc": 2 if _sget(ss, "niv") in ("M", "1", "2") else 1,
        "gender_enc":       1 if str(_sget(ss, "sexe", "")).lower().startswith("f") else 0,
        "age_approx":       float(_sget(ss, "age", 65) or 65),
        "n_vital_measures": len(reevs) * 6 + 6,  # 6 vitaux par réév + base
    }


def build_readmission_prefill(ss) -> dict:
    """Pré-remplit le formulaire LACE depuis le contexte patient.

    Returns:
        dict avec :
            urgence_admission     — bool : True si triage M/1/2
            comorbidites_charlson — list[str] : clés Charlson dérivées des ATCD
            age                   — int
            sexe                  — "Homme" | "Femme" | ""
    """
    atcd = _sget(ss, "atcd", []) or []
    niv  = _sget(ss, "niv", "")
    return {
        "urgence_admission":     niv in ("M", "1", "2", "3A"),
        "comorbidites_charlson": atcd_to_charlson(atcd),
        "age":                   int(_sget(ss, "age", 50) or 50),
        "sexe":                  str(_sget(ss, "sexe", "") or ""),
        "anticoag":              atcd_contains_anticoag(atcd),
    }
