import pytest
from sqlalchemy import inspect, select

from app.models.player import Player
from app.models.player_season_stat import PlayerSeasonStat
from app.models.team import Team
from app.services.clients.types import (
    ApiNbaPlayerProfileData,
    PlayerSeasonData,
)
from app.services.repositories.player_seasons import (
    list_player_seasons,
    upsert_player_season,
)


API_PLAYER: ApiNbaPlayerProfileData = {
    "api_nba_id": 417,
    "name": "Stephen Curry",
    "position": "G",
    "jersey_number": "30",
}

UPDATED_2025_ROW: PlayerSeasonData = {
    "api_nba_id": 417,
    "season": "2025-26",
    "primary_team_abbr": "GSW",
    "games_played": 79,
    "pts": 25.4,
    "reb": 4.5,
    "ast": 6.1,
    "stl": 1.0,
    "blk": 0.4,
    "fg_pct": 0.47,
    "fg3_pct": 0.41,
    "ft_pct": 0.92,
    "mins": 33.2,
    "recent_games": 10,
}


def make_team(abbr: str = "GSW") -> Team:
    return Team(
        abbr=abbr,
        nba_id=1610612744,
        balldontlie_id=10,
        api_nba_id=None,
        name="Warriors",
        city="Golden State",
        record="0-0",
    )


def make_player(name: str = "Stephen Curry") -> Player:
    return Player(
        nba_id=201939,
        balldontlie_id=115,
        api_nba_id=None,
        name=name,
        team_abbr="GSW",
        position="G",
        jersey_number="30",
        games_played=0,
        pts=0,
        reb=0,
        ast=0,
        stl=0,
        blk=0,
        fg_pct=0,
        fg3_pct=0,
        ft_pct=0,
        mins=0,
        recent_games=0,
    )


def test_models_expose_separate_provider_ids() -> None:
    assert {column.name for column in inspect(Team).columns} >= {
        "nba_id",
        "balldontlie_id",
        "api_nba_id",
    }
    assert {column.name for column in inspect(Player).columns} >= {
        "nba_id",
        "balldontlie_id",
        "api_nba_id",
    }


@pytest.mark.asyncio
async def test_upsert_replaces_only_requested_season(db_session) -> None:
    team = make_team()
    player = make_player()
    stale_player = make_player("Stale Player")
    stale_player.nba_id = 999
    stale_player.balldontlie_id = 999
    db_session.add_all([team, player, stale_player])
    await db_session.flush()
    db_session.add_all([
        PlayerSeasonStat(
            player_id=player.id,
            season="2024-25",
            primary_team_abbr="GSW",
            games_played=70,
            pts=24.0,
            reb=4.0,
            ast=6.0,
            stl=1.0,
            blk=0.4,
            fg_pct=0.45,
            fg3_pct=0.40,
            ft_pct=0.9,
            mins=32.0,
            recent_games=10,
        ),
        PlayerSeasonStat(
            player_id=player.id,
            season="2025-26",
            primary_team_abbr="GSW",
            games_played=1,
            pts=1.0,
            reb=1.0,
            ast=1.0,
            stl=0.0,
            blk=0.0,
            fg_pct=0.1,
            fg3_pct=0.1,
            ft_pct=0.1,
            mins=1.0,
            recent_games=1,
        ),
        PlayerSeasonStat(
            player_id=stale_player.id,
            season="2025-26",
            primary_team_abbr="GSW",
            games_played=1,
            pts=2.0,
            reb=0,
            ast=0,
            stl=0,
            blk=0,
            fg_pct=0,
            fg3_pct=0,
            ft_pct=0,
            mins=1,
            recent_games=1,
        ),
    ])
    await db_session.commit()

    inserted, updated = await upsert_player_season(
        db_session,
        season="2025-26",
        teams=[{"api_nba_id": 10, "abbr": "GSW"}],
        profiles=[API_PLAYER],
        rows=[UPDATED_2025_ROW],
    )
    await db_session.commit()

    assert (inserted, updated) == (0, 1)
    seasons = (
        await db_session.execute(
            select(PlayerSeasonStat).order_by(PlayerSeasonStat.season)
        )
    ).scalars().all()
    assert [row.season for row in seasons] == ["2024-25", "2025-26"]
    assert seasons[1].pts == 25.4
    assert seasons[1].player_id == player.id
    await db_session.refresh(player)
    await db_session.refresh(team)
    assert player.api_nba_id == 417
    assert player.nba_id == 201939
    assert player.balldontlie_id == 115
    assert team.api_nba_id == 10
    assert team.nba_id == 1610612744
    assert team.balldontlie_id == 10


@pytest.mark.asyncio
async def test_repeated_import_updates_without_duplicate(db_session) -> None:
    db_session.add(make_team())
    await db_session.commit()

    first = await upsert_player_season(
        db_session,
        season="2025-26",
        teams=[{"api_nba_id": 10, "abbr": "GSW"}],
        profiles=[API_PLAYER],
        rows=[UPDATED_2025_ROW],
    )
    await db_session.commit()
    second = await upsert_player_season(
        db_session,
        season="2025-26",
        teams=[{"api_nba_id": 10, "abbr": "GSW"}],
        profiles=[API_PLAYER],
        rows=[{**UPDATED_2025_ROW, "pts": 26.0}],
    )
    await db_session.commit()

    assert first == (1, 0)
    assert second == (0, 1)
    players = (await db_session.execute(select(Player))).scalars().all()
    rows = (await db_session.execute(select(PlayerSeasonStat))).scalars().all()
    assert len(players) == len(rows) == 1
    assert rows[0].pts == 26.0


@pytest.mark.asyncio
async def test_invalid_input_is_rejected_before_existing_rows_are_deleted(db_session) -> None:
    team = make_team()
    player = make_player()
    db_session.add_all([team, player])
    await db_session.flush()
    existing = PlayerSeasonStat(
        player_id=player.id,
        season="2025-26",
        primary_team_abbr="GSW",
        games_played=1,
        pts=10,
        reb=1,
        ast=1,
        stl=0,
        blk=0,
        fg_pct=0.5,
        fg3_pct=0.4,
        ft_pct=0.8,
        mins=20,
        recent_games=1,
    )
    db_session.add(existing)
    await db_session.commit()

    with pytest.raises(ValueError, match="team"):
        await upsert_player_season(
            db_session,
            season="2025-26",
            teams=[{"api_nba_id": 10, "abbr": "GSW"}],
            profiles=[API_PLAYER],
            rows=[{**UPDATED_2025_ROW, "primary_team_abbr": "BOS"}],
        )

    assert (
        await db_session.execute(select(PlayerSeasonStat))
    ).scalar_one().id == existing.id


@pytest.mark.asyncio
async def test_list_player_seasons_returns_distinct_descending_values(db_session) -> None:
    team = make_team()
    player = make_player()
    db_session.add_all([team, player])
    await db_session.flush()
    for season in ("2024-25", "2025-26"):
        db_session.add(PlayerSeasonStat(
            player_id=player.id,
            season=season,
            primary_team_abbr="GSW",
            games_played=1,
            pts=0,
            reb=0,
            ast=0,
            stl=0,
            blk=0,
            fg_pct=0,
            fg3_pct=0,
            ft_pct=0,
            mins=0,
            recent_games=1,
        ))
    await db_session.commit()

    assert await list_player_seasons(db_session) == ["2025-26", "2024-25"]
