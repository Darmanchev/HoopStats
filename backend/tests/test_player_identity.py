from app.services import player_identity


def test_registry_resolves_imported_names_without_using_provider_ids():
    assert player_identity.resolve_nba_id("Stephen Curry", None) == 201939
    assert player_identity.resolve_nba_id("Unknown Player", None) is None
    assert player_identity.resolve_nba_id("Unknown Player", 123) == 123


def test_accented_names_and_ambiguous_names(monkeypatch):
    monkeypatch.setattr(player_identity, "get_players", lambda: [
        {"id": 1, "full_name": "Nikola Jokic"},
        {"id": 2, "full_name": "Same Name"},
        {"id": 3, "full_name": "Same Name"},
    ])
    player_identity.official_player_ids.cache_clear()
    try:
        assert player_identity.resolve_nba_id("Nikola Jokić", None) == 1
        assert player_identity.resolve_nba_id("Same Name", None) is None
    finally:
        player_identity.official_player_ids.cache_clear()
