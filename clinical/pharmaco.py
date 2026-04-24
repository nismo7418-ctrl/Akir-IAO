# clinical/pharmaco.py – modifications principales : import utilitaire, posologie Buccolam

from clinical.utils import norm   # <- centralisé
# ... (autres imports identiques)

# Fonctions inchangées, sauf :

def protocole_epilepsie_ped(
    poids: float, age: float, duree_min: float,
    en_cours: bool, atcd: list,
    gl: Optional[float] = None,
) -> dict:
    # ...
    # Buccolam® – volumes par tranche d'âge STRICT (AMM), PAS de calcul pondéral
    if   age < 1:   buccolam_dose_mg = 2.5 ; buccolam_vol = "0,5 ml"
    elif age < 5:   buccolam_dose_mg = 5.0 ; buccolam_vol = "1 ml"
    elif age < 10:  buccolam_dose_mg = 7.5 ; buccolam_vol = "1,5 ml"
    else:           buccolam_dose_mg = 10.0; buccolam_vol = "2 ml"

    # Ligne 1a – Midazolam buccal (corrigée)
    ligne1a = {"med": "Midazolam buccal (Buccolam®)",
               "dose_mg": buccolam_dose_mg,
               "volume": buccolam_vol,
               "admin": "Déposer entre la gencive et la joue",
               "delai": "Effet en 5-10 min", "peut_repeter": "1 seule dose",
               "ref": "BCFI — Midazolam buccal (Buccolam)"}

    # Ligne 1b, 1c, etc. restent inchangées (calcul au poids autorisé pour les autres voies)
    # ...