from unittest.mock import AsyncMock

import pytest

from app.models.player import Player
from app.models.team import Team
from app.services.repositories import players as players_repo
from app.services.repositories import teams as teams_repo


class ScalarResult:
    def __init__(self, value: object) -> None:
        self.value = value

    def scalar_one_or_none(self) -> object:
        return self.value

    def scalars(self) -> "ScalarResult":
        return self

    def all(self) -> list[object]:
        if self.value is None:
            return []
        if isinstance(self.value, list):
            return self.value
        return [self.value]


class SequenceSession:
    def __init__(self, *results: object) -> None:
        self.results = iter(results)
        self.added: list[object] = []
        self.commit = AsyncMock()

    async def execute(self, _statement: object) -> ScalarResult:
        return ScalarResult(next(self.results))

    def add(self, value: object) -> None:
        self.added.append(value)


@pytest.mark.asyncio
async def test_team_upsert_preserves_official_and_standings_fields() -> None:
    team = Team(
        abbr="BOS",
        nba_id=1610612738,
        balldontlie_id=None,
        name="Old Name",
        city="Old City",
        record="52-20",
        conference="East",
        conference_rank=2,
        last_ten="8-2",
        streak="W3",
    )
    session = SequenceSession(team)

    count = await teams_repo.upsert_teams(session, [{
        "balldontlie_id": 2,
        "abbr": "BOS",
        "city": "Boston",
        "name": "Celtics",
        "conference": "East",
    }])

    assert count == 0
    assert team.nba_id == 1610612738
    assert team.balldontlie_id == 2
    assert (team.name, team.city) == ("Celtics", "Boston")
    assert team.record == "52-20"
    assert team.last_ten == "8-2"
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_new_team_uses_neutral_standings_defaults() -> None:
    session = SequenceSession(None)

    count = await teams_repo.upsert_teams(session, [{
        "balldontlie_id": 14,
        "abbr": "LAL",
        "city": "Los Angeles",
        "name": "Lakers",
        "conference": "West",
    }])

    assert count == 1
    team = session.added[0]
    assert isinstance(team, Team)
    assert team.nba_id is None
    assert team.balldontlie_id == 14
    assert team.record == "0-0"
    assert team.conference_rank is None
    assert team.last_ten is None
    assert team.streak is None
    session.commit.assert_not_awaited()


def make_player(
    *,
    name: str = "Stephen Curry",
    team_abbr: str = "GSW",
    balldontlie_id: int | None = None,
) -> Player:
    return Player(
        id=1,
        nba_id=201939,
        balldontlie_id=balldontlie_id,
        name=name,
        team_abbr=team_abbr,
        position="G",
        jersey_number="30",
        games_played=70,
        pts=29.4,
        reb=5.1,
        ast=6.3,
        stl=1.0,
        blk=0.4,
        fg_pct=0.49,
        fg3_pct=0.42,
        ft_pct=0.91,
        mins=34.0,
        recent_games=10,
    )


@pytest.mark.asyncio
async def test_player_upsert_by_provider_id_preserves_stats_and_nba_id() -> None:
    player = make_player(balldontlie_id=115)
    session = SequenceSession(player)

    created, updated = await players_repo.upsert_players(session, [{
        "balldontlie_id": 115,
        "name": "Stephen Curry",
        "team_abbr": "GSW",
        "position": "PG",
        "jersey_number": "30",
    }])

    assert (created, updated) == (0, 1)
    assert player.nba_id == 201939
    assert player.pts == 29.4
    assert player.position == "PG"
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_first_player_sync_attaches_exact_name_and_team_match() -> None:
    player = make_player()
    session = SequenceSession(None, player)

    created, updated = await players_repo.upsert_players(session, [{
        "balldontlie_id": 115,
        "name": " Stephen   Curry ",
        "team_abbr": "GSW",
        "position": "G",
        "jersey_number": "30",
    }])

    assert (created, updated) == (0, 1)
    assert player.balldontlie_id == 115
    assert session.added == []


@pytest.mark.asyncio
async def test_same_player_name_on_different_team_inserts_new_row() -> None:
    session = SequenceSession(None, None)

    created, updated = await players_repo.upsert_players(session, [{
        "balldontlie_id": 9001,
        "name": "Stephen Curry",
        "team_abbr": "BOS",
        "position": "G",
        "jersey_number": None,
    }])

    assert (created, updated) == (1, 0)
    player = session.added[0]
    assert isinstance(player, Player)
    assert player.nba_id is None
    assert player.team_abbr == "BOS"
    assert player.games_played == 0
    assert player.pts == 0.0
    session.commit.assert_not_awaited()
