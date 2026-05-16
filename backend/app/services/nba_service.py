import time
import httpx
from datetime import datetime
from nba_api.stats.static import teams as nba_teams
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.endpoints import leaguestandings
from nba_api.stats.endpoints import leaguegamefinder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.team_stats import TeamStats
from ..models.team import Team
from ..models.game import Game
from ..models.injury import Injury


def determine_season_type(date_str: str) -> str:
    """
    NBA Playoffs start mid-April (14-20) and end in June.
    Regular season runs from October to mid-April.
    Handles multiple date formats from NBA API.
    """
    try:
        # Try parsing ISO format: "2026-05-11" or "2026-05-11T00:00:00"
        if "T" in date_str:
            date_str = date_str.split("T")[0]
        
        # Try standard date parsing
        for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%m/%d/%Y"):
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                # Playoffs: April 14+ through June
                if dt.month == 4 and dt.day >= 14:
                    return "playoffs"
                if dt.month in (5, 6):
                    return "playoffs"
                return "regular"
            except ValueError:
                continue
        
        # Fallback: try to extract month from string
        date_lower = date_str.lower()
        if any(m in date_lower for m in ["may", "june"]):
            return "playoffs"
        if "april" in date_lower:
            try:
                day = int(date_str.split()[1].replace(",", ""))
                if day >= 14:
                    return "playoffs"
            except (ValueError, IndexError):
                pass
        
        return "regular"
    except Exception:
        return "regular"

# цвета команд — храним сами
TEAM_COLORS = {
    "ATL": {"color": "#C8102E", "accent": "#FDB927"},
    "BOS": {"color": "#006532", "accent": "#9DC535"},
    "BKN": {"color": "#000000", "accent": "#FFFFFF"},
    "CHA": {"color": "#1D1160", "accent": "#00788C"},
    "CHI": {"color": "#CE1141", "accent": "#000000"},
    "CLE": {"color": "#860038", "accent": "#FDBB30"},
    "DAL": {"color": "#00538C", "accent": "#002B5E"},
    "DEN": {"color": "#0E2240", "accent": "#FEC524"},
    "DET": {"color": "#C8102E", "accent": "#1D42BA"},
    "GSW": {"color": "#1D428A", "accent": "#FFC72C"},
    "HOU": {"color": "#CE1141", "accent": "#000000"},
    "IND": {"color": "#002D62", "accent": "#FDBB30"},
    "LAC": {"color": "#7B1028", "accent": "#1168C4"},
    "LAL": {"color": "#3B1F6B", "accent": "#FDB927"},
    "MEM": {"color": "#5D76A9", "accent": "#12173F"},
    "MIA": {"color": "#8B0022", "accent": "#F9A01B"},
    "MIL": {"color": "#003313", "accent": "#A3D55C"},
    "MIN": {"color": "#0C2340", "accent": "#236192"},
    "NOP": {"color": "#0C2340", "accent": "#85714D"},
    "NYK": {"color": "#005BA1", "accent": "#F58426"},
    "OKC": {"color": "#00599C", "accent": "#EF3B24"},
    "ORL": {"color": "#0077C0", "accent": "#C4CED4"},
    "PHI": {"color": "#006BB6", "accent": "#ED174C"},
    "PHX": {"color": "#1D1160", "accent": "#E56020"},
    "POR": {"color": "#E03A3E", "accent": "#000000"},
    "SAC": {"color": "#5A2D81", "accent": "#63727A"},
    "SAS": {"color": "#C4CED4", "accent": "#000000"},
    "TOR": {"color": "#CE1141", "accent": "#000000"},
    "UTA": {"color": "#002B5C", "accent": "#F9A01B"},
    "WAS": {"color": "#002B5C", "accent": "#E31837"},
}

async def sync_teams(db: AsyncSession):
    """Загружает все команды из NBA API в базу"""
    all_teams = nba_teams.get_teams()

    # получаем рекорды из standings
    standings = leaguestandings.LeagueStandings(season="2025-26")
    data = standings.get_dict()
    headers = data["resultSets"][0]["headers"]
    rows = data["resultSets"][0]["rowSet"]

    records = {}
    for row in rows:
        s = dict(zip(headers, row))
        records[int(s["TeamID"])] = f"{s.get('WINS', 0)}-{s.get('LOSSES', 0)}"

    for t in all_teams:
        abbr = t["abbreviation"]
        colors = TEAM_COLORS.get(abbr, {"color": "#000000", "accent": "#FFFFFF"})
        record = records.get(int(t["id"]), "0-0")

        existing = await db.execute(select(Team).where(Team.abbr == abbr))
        team = existing.scalar_one_or_none()

        if not team:
            db.add(Team(
                abbr=abbr,
                nba_id=t["id"],
                name=t["nickname"],
                city=t["city"],
                color=colors["color"],
                accent=colors["accent"],
                record=record,
            ))
        else:
            team.record = record
            team.nba_id = t["id"]

    await db.commit()
    print(f"Синхронизировано {len(all_teams)} команд")

async def sync_games(db: AsyncSession):
    """Загружает живые игры сегодня"""
    try:
        board = scoreboard.ScoreBoard(
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'Referer': 'https://www.nba.com/',
                'Origin': 'https://www.nba.com',
            }
        )
        data = board.get_dict()
        games = data.get("scoreboard", {}).get("games", [])

        if not games:
            print("Сегодня игр нет")
            return

        for g in games:
            game_id = str(g["gameId"])
            home = g["homeTeam"]
            away = g["awayTeam"]
            status = g["gameStatusText"]
            is_final = "Final" in status

            existing = await db.execute(select(Game).where(Game.id == game_id))
            game = existing.scalar_one_or_none()

            if not game:
                db.add(Game(
                    id=game_id,
                    team1=away["teamTricode"],
                    team2=home["teamTricode"],
                    date=g["gameEt"][:10],
                    time=status,
                    venue=g.get("arenaName", ""),
                    is_today=True,
                    season_type=determine_season_type(g["gameEt"]),
                    score1=away["score"] if is_final else None,
                    score2=home["score"] if is_final else None,
                ))
            elif is_final:
                game.score1 = away["score"]
                game.score2 = home["score"]

        await db.commit()
        print(f"Синхронизировано {len(games)} игр")

    except Exception as e:
        print(f"Ошибка при загрузке игр: {e}")

async def get_team_form(team_id: int) -> dict:
    """Возвращает форму команды и последние счета"""
    # небольшая пауза чтобы не попасть под rate limit
    time.sleep(0.6)
    log = teamgamelog.TeamGameLog(
        team_id=str(team_id),
        season="2024-25"
    )
    data = log.get_dict()
    headers = data["resultSets"][0]["headers"]
    rows = data["resultSets"][0]["rowSet"][:10]

    form = []
    scores = []
    for row in rows:
        game = dict(zip(headers, row))
        form.append(game["WL"])
        scores.append(int(game["PTS"]))

    return {
        "form": form[:5],        # последние 5 W/L
        "last_scores": scores,   # последние 10 счетов
    }

async def sync_team_stats(db: AsyncSession):
    """Загружает форму и последние счета для всех команд"""
    result = await db.execute(select(Team))
    teams = result.scalars().all()

    for team in teams:
        if not team.nba_id:
            continue

        try:
            time.sleep(0.6)  # rate limit
            log = teamgamelog.TeamGameLog(
                team_id=str(team.nba_id),
                season="2025-26",
            )
            data = log.get_dict()
            headers = data["resultSets"][0]["headers"]
            rows = data["resultSets"][0]["rowSet"][:10]

            form = []
            scores = []
            for row in rows:
                game = dict(zip(headers, row))
                form.append(game["WL"])
                scores.append(int(game["PTS"]))

            existing = await db.execute(
                select(TeamStats).where(TeamStats.team_abbr == team.abbr)
            )
            stats = existing.scalar_one_or_none()

            if not stats:
                db.add(TeamStats(
                    team_abbr=team.abbr,
                    form=form[:5],
                    last_scores=scores,
                ))
            else:
                stats.form = form[:5]
                stats.last_scores = scores

            print(f"{team.abbr} — {form[:5]}")

        except Exception as e:
            print(f"Ошибка {team.abbr}: {e}")

    await db.commit()
    print("Статистика команд синхронизирована")


async def sync_historical_games(db: AsyncSession, season: str = "2025-26"):
    """Загружает все игры сезона (regular + playoffs)"""
    print(f"Загрузка игр сезона {season}...")
    
    # Загружаем регулярный сезон
    finder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        season_type_nullable="Regular Season",
    )
    data = finder.get_dict()
    headers = data["resultSets"][0]["headers"]
    rows = data["resultSets"][0]["rowSet"]

    # каждая игра есть дважды (за каждую команду) — берём уникальные
    seen = set()
    count = 0

    for row in rows:
        g = dict(zip(headers, row))
        game_id = str(g["GAME_ID"])

        if game_id in seen:
            continue
        seen.add(game_id)

        # ищем пару для этой игры
        pair = [r for r in rows if dict(zip(headers, r))["GAME_ID"] == game_id]
        if len(pair) < 2:
            continue

        g1 = dict(zip(headers, pair[0]))
        g2 = dict(zip(headers, pair[1]))

        existing = await db.execute(select(Game).where(Game.id == game_id))
        if existing.scalar_one_or_none():
            continue

        db.add(Game(
            id=game_id,
            team1=g1["TEAM_ABBREVIATION"],
            team2=g2["TEAM_ABBREVIATION"],
            date=g1["GAME_DATE"],
            time="Final",
            venue="",
            is_today=False,
            season_type=determine_season_type(g1["GAME_DATE"]),
            score1=int(g1["PTS"]) if g1["PTS"] else None,
            score2=int(g2["PTS"]) if g2["PTS"] else None,
        ))
        count += 1

    await db.commit()
    print(f"Загружено {count} игр регулярного сезона")

    # Загружаем плей-офф
    await _sync_playoffs(db, season)


async def _sync_playoffs(db: AsyncSession, season: str):
    """Загружает игры плей-офф"""
    print(f"Загрузка игр плей-офф сезона {season}...")
    
    try:
        finder = leaguegamefinder.LeagueGameFinder(
            season_nullable=season,
            season_type_nullable="Playoffs",
        )
    except Exception:
        print("Плей-офф ещё не начался или данные недоступны")
        return
    
    data = finder.get_dict()
    if not data.get("resultSets") or not data["resultSets"][0].get("rowSet"):
        print("Игр плей-офф не найдено")
        return
    
    headers = data["resultSets"][0]["headers"]
    rows = data["resultSets"][0]["rowSet"]
    
    seen = set()
    count = 0
    
    for row in rows:
        g = dict(zip(headers, row))
        game_id = str(g["GAME_ID"])
        
        if game_id in seen:
            continue
        seen.add(game_id)
        
        pair = [r for r in rows if dict(zip(headers, r))["GAME_ID"] == game_id]
        if len(pair) < 2:
            continue
        
        g1 = dict(zip(headers, pair[0]))
        g2 = dict(zip(headers, pair[1]))
        
        existing = await db.execute(select(Game).where(Game.id == game_id))
        if existing.scalar_one_or_none():
            continue
        
        db.add(Game(
            id=game_id,
            team1=g1["TEAM_ABBREVIATION"],
            team2=g2["TEAM_ABBREVIATION"],
            date=g1["GAME_DATE"],
            time="Final",
            venue="",
            is_today=False,
            season_type="playoffs",
            score1=int(g1["PTS"]) if g1["PTS"] else None,
            score2=int(g2["PTS"]) if g2["PTS"] else None,
        ))
        count += 1
    
    await db.commit()
    print(f"Загружено {count} игр плей-офф")


async def sync_injuries(db: AsyncSession):
    """Загружает травмы всех игроков из ESPN API"""
    print("Загрузка данных о травмах из ESPN...")
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries",
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"Ошибка при загрузке травм: {e}")
        return
    
    athletes = data.get("sports", [{}])[0].get("leagues", [{}])[0].get("athletes", [])
    
    # Очищаем старые травмы
    result = await db.execute(select(Injury))
    existing = result.scalars().all()
    for inj in existing:
        await db.delete(inj)
    await db.commit()
    
    count = 0
    for entry in athletes:
        athlete = entry.get("athlete", {})
        details = entry.get("details", {})
        notes = entry.get("notes", {})
        team = athlete.get("team", {})
        position = athlete.get("position", {})
        
        # Статус: Out, Day-To-Day, Questionable, Doubtful
        status = entry.get("status", "Out")
        if status == "Out":
            status = "Out"
        elif status == "Day-To-Day":
            status = "Day-to-Day"
        elif status == "Questionable":
            status = "Questionable"
        elif status == "Doubtful":
            status = "Doubtful"
        else:
            status = "Out"
        
        # Тип травмы
        injury_type = details.get("type", "Not Specified")
        injury_detail = details.get("detail", "")
        injury_desc = f"{injury_type} {injury_detail}".strip() if injury_detail else injury_type
        
        # Комментарий
        comment = ""
        items = notes.get("items", [])
        if items:
            comment = items[0].get("headline", "")
        
        db.add(Injury(
            team_abbr=team.get("abbreviation", "UNK"),
            player_name=athlete.get("displayName", "Unknown"),
            position=position.get("abbreviation", "N/A"),
            injury=injury_desc,
            status=status,
        ))
        count += 1
    
    await db.commit()
    print(f"Загружено {count} записей о травмах")