from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.player import Player
from app.models.player_season_stat import PlayerSeasonStat
from app.models.team import Team
from app.routers import players


async def insert_player_seasons(
    db_session: AsyncSession,
    seasons: list[str],
) -> Player:
    db_session.add(Team(
        abbr="GSW",
        nba_id=1610612744,
        balldontlie_id=10,
        api_nba_id=10,
        name="Warriors",
        city="Golden State",
        record="0-0",
    ))
    player = Player(
        nba_id=None,
        balldontlie_id=115,
        api_nba_id=417,
        name="Stephen Curry",
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
    db_session.add(player)
    await db_session.flush()
    db_session.add_all([
        PlayerSeasonStat(
            player_id=player.id,
            season=season,
            primary_team_abbr="GSW",
            games_played=79,
            pts=26.4,
            reb=4.5,
            ast=6.1,
            stl=1.0,
            blk=0.4,
            fg_pct=0.47,
            fg3_pct=0.41,
            ft_pct=0.92,
            mins=33.2,
            recent_games=10,
        )
        for season in seasons
    ])
    await db_session.commit()
    return player


@pytest.mark.asyncio
async def test_season_position_filter_uses_snapshot_and_hybrid_group(db_session, players_client):
    player = await insert_player_seasons(db_session, ["2024-25"])
    player.position = "C"
    row = (await db_session.execute(select(PlayerSeasonStat))).scalar_one()
    row.position = "G-F"
    row.jersey_number = "12"
    await db_session.commit()
    for position in ("G", "F"):
        response = await players_client.get(f"/players/?season=2024-25&position={position}")
        assert response.status_code == 200
        assert response.json()[0]["position"] == "G-F"
        assert response.json()[0]["jerseyNumber"] == "12"
    response = await players_client.get("/players/?season=2024-25&position=C")
    assert response.json() == []


@pytest.mark.asyncio
async def test_search_filters_before_pagination(db_session, players_client):
    player = await insert_player_seasons(db_session, ["2024-25"])
    for index in range(205):
        copy = Player(**{column.name: getattr(player, column.name)
                         for column in Player.__table__.columns
                         if column.name not in {"id", "nba_id", "balldontlie_id", "api_nba_id"}})
        copy.name = f"Player {index:03}"
        db_session.add(copy)
    await db_session.commit()
    first = await players_client.get("/players/?sort_by=name&limit=200")
    assert len(first.json()) == 200
    assert all(row["name"] != "Stephen Curry" for row in first.json())
    found = await players_client.get("/players/?sort_by=name&limit=50&search=Curry")
    assert [row["name"] for row in found.json()] == ["Stephen Curry"]
    seasonal = await players_client.get("/players/?season=2024-25&search=Curry")
    assert [row["name"] for row in seasonal.json()] == ["Stephen Curry"]
    last = await players_client.get("/players/?sort_by=name&limit=200&skip=200")
    assert len(last.json()) == 6


class FakeResult:
    def __init__(self, player: Player | None) -> None:
        self.player = player

    def scalar_one_or_none(self) -> Player | None:
        return self.player


class FakeSession:
    def __init__(self, player: Player | None) -> None:
        self.player = player

    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult(self.player)


@pytest.mark.asyncio
async def test_player_detail_exposes_provider_id_without_official_id() -> None:
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
    player.team = Team(
        abbr="GSW",
        nba_id=1610612744,
        balldontlie_id=10,
        name="Warriors",
        city="Golden State",
        record="0-0",
    )
    app = FastAPI()
    app.include_router(players.router)

    async def override_get_db() -> AsyncIterator[FakeSession]:
        yield FakeSession(player)

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/players/1")

    assert response.status_code == 200
    assert response.json()["nbaId"] == 201939
    assert response.json()["balldontlieId"] == 115


@pytest.mark.asyncio
async def test_player_list_uses_selected_season_stats(
    players_client,
    db_session,
) -> None:
    await insert_player_seasons(db_session, ["2025-26"])

    response = await players_client.get(
        "/players/?season=2025-26&sort_by=pts&min_games=10"
    )

    assert response.status_code == 200
    assert response.json()[0] == {
        "id": 1,
        "nbaId": 201939,
        "balldontlieId": 115,
        "apiNbaId": 417,
        "season": "2025-26",
        "name": "Stephen Curry",
        "teamAbbr": "GSW",
        "position": "G",
        "jerseyNumber": "30",
        "gamesPlayed": 79,
        "pts": 26.4,
        "reb": 4.5,
        "ast": 6.1,
        "stl": 1.0,
        "blk": 0.4,
        "fgPct": 0.47,
        "fg3Pct": 0.41,
        "ftPct": 0.92,
        "mins": 33.2,
        "recentGames": 10,
    }


@pytest.mark.asyncio
async def test_unknown_imported_season_returns_empty_list(players_client) -> None:
    response = await players_client.get("/players/?season=1990-91")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_player_seasons_are_reverse_chronological(
    players_client,
    db_session,
) -> None:
    await insert_player_seasons(db_session, ["2024-25", "2025-26"])

    response = await players_client.get("/players/seasons")

    assert response.status_code == 200
    assert response.json() == ["2025-26", "2024-25"]


@pytest.mark.asyncio
async def test_player_detail_uses_selected_season_stats_and_team(
    players_client,
    db_session,
) -> None:
    player = await insert_player_seasons(db_session, ["2025-26"])

    response = await players_client.get(
        f"/players/{player.id}?season=2025-26"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["season"] == "2025-26"
    assert body["pts"] == 26.4
    assert body["teamAbbr"] == "GSW"
    assert body["teamName"] == "Warriors"
    assert body["teamCity"] == "Golden State"


@pytest.mark.asyncio
async def test_player_detail_returns_404_when_season_is_not_imported(
    players_client,
    db_session,
) -> None:
    player = await insert_player_seasons(db_session, ["2025-26"])

    response = await players_client.get(
        f"/players/{player.id}?season=2024-25"
    )

    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("season", ["2025", "2025-27", "bad-value"])
async def test_invalid_season_returns_422(players_client, season: str) -> None:
    list_response = await players_client.get(f"/players/?season={season}")
    detail_response = await players_client.get(f"/players/1?season={season}")

    assert list_response.status_code == 422
    assert detail_response.status_code == 422
