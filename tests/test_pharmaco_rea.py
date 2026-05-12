from pathlib import Path

import clinical.pharmaco_rea as rea


def test_rea_database_counts():
    assert len(rea.get_dilutions()) == 32
    assert len(rea.get_compatibilites()) == 95
    assert len(rea.get_substances_list()) >= 20


def test_rea_dilution_lookup_and_search_are_accent_tolerant():
    levophed = rea.get_dilution("Levophed")
    assert levophed is not None
    assert "noradrénaline" in levophed["DCI"]

    results = rea.search_dilutions("noradrenaline")
    assert [row["nom_source"] for row in results] == ["Levophed"]


def test_rea_compatibility_lookup_in_both_directions_and_dci():
    assert rea.check_compatibility("midazolam", "morphine")["statut"] == "C"
    assert rea.check_compatibility("morphine", "midazolam")["statut"] == "C"
    assert rea.check_compatibility("heparin sodium", "morphine")["statut"] == "I"


def test_rea_missing_json_does_not_crash(monkeypatch):
    old_path = rea._JSON_PATH
    rea._load.cache_clear()
    monkeypatch.setattr(rea, "_JSON_PATH", Path("data/__missing_pharmacie_rea.json"))

    try:
        assert rea.get_dilutions() == []
        assert rea.get_compatibilites() == []
        assert rea.get_dilution("Levophed") is None
        assert rea.check_compatibility("midazolam", "morphine") is None
    finally:
        monkeypatch.setattr(rea, "_JSON_PATH", old_path)
        rea._load.cache_clear()
