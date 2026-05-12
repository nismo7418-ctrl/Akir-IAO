from clinical.compatibility import check_iv_compatibility, med_from_perfusion_choice


def test_perf_choice_maps_to_hug_name():
    assert med_from_perfusion_choice("Morphine PSE — Analgésie IV continue") == "morphine"
    assert med_from_perfusion_choice("Adrénaline IV — Anaphylaxie / Choc") == "épinéphrine"


def test_hug_incompatible_pair():
    result = check_iv_compatibility("amiodarone", "furosémide")

    assert result["statut"] == "Incompatible"
    assert result["code"] == "I"
    assert "précipitation" in result["message"].lower() or "précipitation" in result["precision"].lower()


def test_unknown_pair_returns_prudence():
    result = check_iv_compatibility("piritramide", "magnésium")

    assert result["statut"] == "Prudence"
