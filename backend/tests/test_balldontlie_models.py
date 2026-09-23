from app.models.player import Player
from app.models.team import Team
from app.schemas.player import PlayerSchema


def test_provider_ids_are_separate_from_official_nba_ids() -> None:
    team = Team(
        abbr="BOS",
        nba_id=1610612738,
        balldontlie_id=2,
        name="Celtics",
        city="Boston",
        record="0-0",
    )
    player = Player(
        id=1,
        nba_id=None,
        balldontlie_id=115,
        name="Stephen Curry",
        team_abbr="GSW",
        position="G",
        jersey_number="30",
        games_played=0,
        pts=0.0,
        reb=0.0,
        ast=0.0,
        stl=0.0,
        blk=0.0,
        fg_pct=0.0,
        fg3_pct=0.0,
        ft_pct=0.0,
        mins=0.0,
        recent_games=0,
    )

    payload = PlayerSchema.model_validate(player).model_dump(by_alias=True)

    assert team.nba_id == 1610612738
    assert team.balldontlie_id == 2
    assert payload["nbaId"] is None
    assert payload["balldontlieId"] == 115


def test_provider_identifier_columns_are_nullable_and_unique() -> None:
    team_provider_id = Team.__table__.c.balldontlie_id
    player_provider_id = Player.__table__.c.balldontlie_id

    assert team_provider_id.nullable is True
    assert team_provider_id.unique is True
    assert player_provider_id.nullable is True
    assert player_provider_id.unique is True
    assert Player.__table__.c.nba_id.nullable is True
