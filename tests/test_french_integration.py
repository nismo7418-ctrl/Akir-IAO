import clinical.triage as triage
from clinical.french_v12 import (
    FRENCH_PROTOCOL,
    apply_discriminant_selection,
    get_protocol,
)
from clinical.utils import norm


def test_norm_handles_pdf_symbols_and_slashes():
    assert norm("Fièvre ≤ 3 mois") == "fievre <= 3 mois"
    assert norm("Dyspnée/insuffisance cardiaque") == "dyspnee / insuffisance cardiaque"


def test_all_protocol_motifs_are_connected_to_dispatch():
    missing = [
        item["motif"]
        for item in FRENCH_PROTOCOL
        if norm(item["motif"]) not in triage._MOTIF_INDEX
    ]
    assert missing == []


def test_pdf_aliases_resolve_to_existing_protocols():
    samples = {
        "Douleur thoracique/syndrome coronaire aigu (SCA)": "Douleur thoracique / SCA",
        "Vomissement de sang / hématémèse": "Hématémèse / Rectorragie",
        "Maelena/rectorragies": "Hématémèse / Rectorragie",
        "Fièvre ≤ 3 mois": "Pédiatrie - Fièvre ≤ 3 mois",
        "Problème de grossesse 1er et 2ème trimestre": "Complication grossesse T1/T2",
        "Méno-metrorragie": "Ménorragie / Métrorragie",
    }
    for label, expected in samples.items():
        assert get_protocol(label)["motif"] == expected


def test_apply_discriminant_selection_only_majorates():
    selected = {
        "level": "2",
        "text": "Douleur thoracique typique ou signes d'instabilité",
        "label": "Tri 2 — Douleur thoracique typique ou signes d'instabilité",
    }
    level, just, crit = apply_discriminant_selection("3B", "Évaluation", "Base", selected)
    assert level == "2"
    assert "Critère discriminant FRENCH" in just
    assert crit.startswith("Tri 2")

    level, just, crit = apply_discriminant_selection("1", "Priorité absolue", "Base", selected)
    assert level == "1"
    assert just == "Priorité absolue"
    assert crit.startswith("Tri 2")


def test_new_french_handlers_cover_gyn_obs_and_intoxication():
    assert triage.french_triage("Accouchement imminent", {}, 80, 120, 98, 16, 15, 37, 28, 0, None)[0] == "1"
    assert triage.french_triage("Intoxication médicamenteuse", {}, 80, 120, 98, 16, 15, 37, 28, 0, None)[0] == "3B"
