from typing import Literal, TypedDict


class StandingData(TypedDict):
    record: str
    conference: Literal["East", "West"]
    conference_rank: int
    last_ten: str
    streak: str


class LiveGameData(TypedDict):
    game_id: str
    away_abbr: str
    home_abbr: str
    date: str
    start_time: str
    status: Literal["scheduled", "live", "final"]
    status_text: str
    period: int | None
    clock: str | None
    away_score: int | None
    home_score: int | None
    venue: str


class LivePlayerStatData(TypedDict):
    game_id: str
    nba_id: int
    name: str
    team_abbr: str
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    minutes: float


class TeamProfileData(TypedDict):
    balldontlie_id: int
    abbr: str
    city: str
    name: str
    conference: Literal["East", "West"]


class PlayerProfileData(TypedDict):
    balldontlie_id: int
    name: str
    team_abbr: str
    position: str
    jersey_number: str | None


class GameData(TypedDict):
    game_id: str
    away_abbr: str
    home_abbr: str
    date: str
    start_time: str
    status: Literal["scheduled", "live", "final"]
    status_text: str
    period: int | None
    clock: str | None
    away_score: int | None
    home_score: int | None
    venue: str
    season: str
    season_type: Literal["regular", "playoffs"]


class ApiNbaTeamData(TypedDict):
    api_nba_id: int
    abbr: str


class ApiNbaPlayerProfileData(TypedDict):
    api_nba_id: int
    name: str
    position: str
    jersey_number: str | None


class PlayerSeasonData(TypedDict):
    api_nba_id: int
    season: str
    primary_team_abbr: str
    games_played: int
    pts: float
    reb: float
    ast: float
    stl: float
    blk: float
    fg_pct: float
    fg3_pct: float
    ft_pct: float
    mins: float
    recent_games: int
