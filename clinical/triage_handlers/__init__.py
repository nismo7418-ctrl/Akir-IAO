from .cardio import triage_cardio
from .neuro import triage_neuro
from .pediatrie import triage_pediatrie
from .autres import triage_autres

def resolve_handler(motif):
    m = motif.lower()
    if "cardio" in m or "thoracique" in m: return triage_cardio
    if "neuro" in m or "avc" in m: return triage_neuro
    if "pédiatrie" in m or "enfant" in m: return triage_pediatrie
    return triage_autres
