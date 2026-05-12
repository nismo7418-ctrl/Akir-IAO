from clinical.triage import anonymize_voice_text, process_voice_triage
from ui.triage_tab import apply_voice_triage_to_session


def test_voice_triage_anonymizes_and_maps_sca():
    data = process_voice_triage(
        "Monsieur Dupont Jean 67 ans, oppression rétro-sternale depuis 45 minutes, "
        "EVA 8 sur 10, ATCD stent et diabète, sous Eliquis.",
        use_gpt=False,
    )

    assert "Dupont" not in data["texte_anonymise"]
    assert data["age"] == 67
    assert data["sexe"] == "Masculin"
    assert data["motif"] == "Douleur thoracique / SCA"
    assert data["pqrst"]["severite"] == 8
    assert "Coronaropathie / SCA antérieur" in data["atcd"]
    assert "Anticoagulants/AOD" in data["atcd"]


def test_voice_triage_jargon_oap_omi():
    data = process_voice_triage(
        "Femme 82 ans dyspnée avec OMI et orthopnée depuis hier, "
        "connue insuffisance cardiaque et BPCO.",
        use_gpt=False,
    )

    assert data["motif"] == "Dyspnée / insuffisance cardiaque"
    assert "Insuffisance cardiaque" in data["atcd"]
    assert "BPCO" in data["atcd"]
    assert "Grossesse" not in data["atcd"]


def test_anonymize_voice_text_keeps_age():
    sanitized = anonymize_voice_text("Madame Martin Julie 74 ans présente une chute.")

    assert "Martin" not in sanitized
    assert "Julie" not in sanitized
    assert "74 ans" in sanitized


def test_voice_autofill_sets_pediatric_and_antalgie_flags():
    state = {
        "uid": "TST",
        "sid": "TST",
        "det": {},
        "atcd": [],
        "voice_triage_pending": process_voice_triage(
            "Garçon 12 ans douleur cheville EVA 8 sur 10 depuis chute",
            use_gpt=False,
        ),
    }
    wk = lambda base, scope=None: "__".join(x for x in ["TST", scope, base] if x)

    assert apply_voice_triage_to_session(state, wk)
    assert state["smart_ped_vitals"] is True
    assert state["pharmacie_auto_antalgie"] is True
    assert state["TST__tr_eva"] == "8"
