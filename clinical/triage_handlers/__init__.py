from clinical.triage_handlers.cardio import *
from clinical.triage_handlers.neuro import *
from clinical.triage_handlers.pediatrie import *
from clinical.triage_handlers.autres import *

TRIAGE_DISPATCH = {
    "Arrêt cardio-respiratoire": _triage_acr,
    "Hypotension artérielle": _triage_hypotension,
    "Douleur thoracique / SCA": _triage_sca,
    "Tachycardie / tachyarythmie": _triage_arythmie,
    "Bradycardie / bradyarythmie": _triage_arythmie,
    "Palpitations": _triage_arythmie,
    "Hypertension artérielle": _triage_hta,
    "Allergie / anaphylaxie": _triage_anaphylaxie,
    "AVC / Déficit neurologique": _triage_avc,
    "Traumatisme crânien": _triage_tc,
    "Altération de conscience / Coma": _triage_coma,
    "Convulsions / EME": _triage_convulsions,
    "Céphalée": _triage_cephalee,
    "Malaise": _triage_malaise,
    "Dyspnée / insuffisance respiratoire": _triage_dyspnee,
    "Dyspnée / insuffisance cardiaque": _triage_dyspnee,
    "Douleur abdominale": _triage_abdomen,
    "Fièvre": _triage_fievre,
    "Pédiatrie - Fièvre <= 3 mois": _triage_fievre_nourr,
    "Pédiatrie - Fièvre enfant (3 mois - 15 ans)": _triage_ped_fievre,
    "Pédiatrie - Vomissements / Gastro-entérite": _triage_ped_gastro,
    "Pédiatrie - Crise épileptique": _triage_ped_epilepsie,
    "Pétéchie / Purpura": _triage_purpura,
    "Traumatisme thorax/abdomen/rachis cervical": _triage_trauma_axial,
    "Traumatisme bassin/hanche/fémur": _triage_trauma_axial,
    "Traumatisme membre / épaule": _triage_trauma_distal,
    "Hypoglycémie": _triage_hypoglycemie,
    "Hyperglycémie / Cétoacidose": _triage_hyperglycemie,
    "Renouvellement ordonnance": _triage_non_urgent,
    "Examen administratif": _triage_non_urgent,
}

def resolve_handler(motif: str):
    return TRIAGE_DISPATCH.get(motif)
