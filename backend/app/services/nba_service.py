import asyncio
import httpx
from datetime import datetime
from nba_api.stats.static import teams as nba_teams
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.endpoints import leaguestandings
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.endpoints import leaguedashplayerstats
from nba_api.stats.endpoints import commonplayerinfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.team_stats import TeamStats
from ..models.team import Team
from ..models.game import Game
from ..models.injury import Injury
from ..models.player import Player


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
    print(f"NBA API вернул {len(all_teams)} команд")

    # получаем рекорды из standings
    try:
        standings = leaguestandings.LeagueStandings(season="2025-26")
        data = standings.get_dict()
        headers = data["resultSets"][0]["headers"]
        rows = data["resultSets"][0]["rowSet"]
        print(f"Standings: {len(rows)} команд")
    except Exception as e:
        print(f"Ошибка при загрузке standings: {e}")
        rows = []

    records = {}
    for row in rows:
        s = dict(zip(headers, row))
        records[int(s["TeamID"])] = f"{s.get('WINS', 0)}-{s.get('LOSSES', 0)}"

    count = 0
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
            count += 1
        else:
            team.record = record
            team.nba_id = t["id"]

    await db.commit()
    print(f"Синхронизировано {len(all_teams)} команд ({count} новых)")

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
    await asyncio.sleep(0.6)
    log = teamgamelog.TeamGameLog(
        team_id=str(team_id),
        season="2025-26"
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
    print(f"Загрузка статистики для {len(teams)} команд...")

    success_count = 0
    error_count = 0

    for team in teams:
        if not team.nba_id:
            continue

        try:
            await asyncio.sleep(1.0)  # rate limit — увеличена пауза
            log = teamgamelog.TeamGameLog(
                team_id=str(team.nba_id),
                season="2025-26",
            )
            data = log.get_dict()
            result_sets = data.get("resultSets", [])
            if not result_sets:
                print(f"{team.abbr}: нет данных в response")
                error_count += 1
                continue
            
            headers = result_sets[0].get("headers", [])
            rows = result_sets[0].get("rowSet", [])[:10]
            
            if not rows:
                print(f"{team.abbr}: нет игр в логе")
                error_count += 1
                continue

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

            success_count += 1

        except Exception as e:
            error_count += 1
            if error_count <= 3:
                print(f"Ошибка {team.abbr}: {type(e).__name__}: {e}")

    await db.commit()
    print(f"Статистика команд синхронизирована: {success_count} успешно, {error_count} ошибок")


async def sync_historical_games(db: AsyncSession, season: str = "2025-26"):
    """Загружает все игры сезона (regular + playoffs)
    
    NBA API использует формат года начала сезона:
    - "2025" = сезон 2025-26
    - "2024" = сезон 2024-25
    """
    print(f"Загрузка игр сезона {season}...")
    
    # Загружаем регулярный сезон
    try:
        await asyncio.sleep(1.0)
        finder = leaguegamefinder.LeagueGameFinder(
            season_nullable=season,
            season_type_nullable="Regular Season",
        )
        data = finder.get_dict()
    except Exception as e:
        print(f"Ошибка при запросе регулярного сезона: {type(e).__name__}: {e}")
        return
    
    result_sets = data.get("resultSets", [])
    if not result_sets:
        print(f"NBA API вернул пустой response для сезона {season}")
        print(f"Response keys: {list(data.keys())}")
        print(f"Response preview: {str(data)[:300]}")
        return
    
    headers = result_sets[0].get("headers", [])
    rows = result_sets[0].get("rowSet", [])
    print(f"NBA API вернул {len(rows)} записей (регулярный сезон)")
    
    if not rows:
        print(f"Нет данных для сезона {season}. Попробуйте другой год (2024, 2023...)")
        return

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
            season=season,
            season_type="regular",  # NBA API уже отфильтровал "Regular Season"
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
        data = finder.get_dict()
    except Exception as e:
        print(f"Плей-офф ещё не начался или данные недоступны: {e}")
        return
    
    result_sets = data.get("resultSets", [])
    if not result_sets:
        print("Игр плей-офф не найдено (пустой response)")
        return
    
    rows = result_sets[0].get("rowSet", [])
    if not rows:
        print("Игр плей-офф не найдено (пустой rowSet)")
        return
    
    print(f"NBA API вернул {len(rows)} записей (плей-офф)")
    
    headers = result_sets[0].get("headers", [])
    
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
            season=season,
            season_type="playoffs",
            score1=int(g1["PTS"]) if g1["PTS"] else None,
            score2=int(g2["PTS"]) if g2["PTS"] else None,
        ))
        count += 1

    await db.commit()
    print(f"Загружено {count} игр плей-офф")


async def sync_injuries(db: AsyncSession):
    """Загружает травмы всех игроков из ESPN API
    
    Структура ESPN:
    {"injuries": [
      {"displayName": "Atlanta Hawks", "injuries": [
        {"status": "Out", "athlete": {"displayName": "Keshon Gilbert", "position": {"abbreviation": "G"}}, ...}
      ]}
    ]}
    """
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
    except httpx.HTTPStatusError as e:
        print(f"HTTP ошибка при загрузке травм: {e.response.status_code} - {e.response.text[:200]}")
        return
    except Exception as e:
        print(f"Ошибка при загрузке травм: {type(e).__name__}: {e}")
        return
    
    teams_injuries = data.get("injuries", [])
    if not teams_injuries:
        print(f"Травм не найдено. Response keys: {list(data.keys())}")
        return
    
    print(f"ESPN вернул {len(teams_injuries)} команд с травмами")
    
    # Очищаем старые травмы
    result = await db.execute(select(Injury))
    existing = result.scalars().all()
    for inj in existing:
        await db.delete(inj)
    await db.commit()
    
    # Маппинг названий команд в аббревиатуры
    TEAM_NAME_TO_ABBR = {
        "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
        "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
        "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
        "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
        "LA Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
        "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
        "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
        "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
        "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
        "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS",
    }
    
    count = 0
    for team_entry in teams_injuries:
        team_name = team_entry.get("displayName", "")
        team_abbr = TEAM_NAME_TO_ABBR.get(team_name, "UNK")
        injuries = team_entry.get("injuries", [])
        
        for inj in injuries:
            athlete = inj.get("athlete", {})
            details = inj.get("details", {})
            
            status = inj.get("status", "Out")
            if status == "Day-To-Day":
                status = "Day-to-Day"
            elif status not in ("Out", "Questionable", "Doubtful"):
                status = "Out"
            
            injury_type = details.get("type", "Not Specified")
            injury_detail = details.get("detail", "")
            injury_desc = f"{injury_type} {injury_detail}".strip() if injury_detail else injury_type
            
            player_name = athlete.get("displayName", "Unknown")
            position = athlete.get("position", {})
            pos_abbr = position.get("abbreviation", "N/A")
            
            try:
                db.add(Injury(
                    team_abbr=team_abbr,
                    player_name=player_name,
                    position=pos_abbr,
                    injury=injury_desc[:100],
                    status=status,
                ))
                count += 1
            except Exception as e:
                print(f"Ошибка при сохранении {player_name}: {e}")
    
    await db.commit()
    print(f"Загружено {count} записей о травмах")


async def sync_players(db: AsyncSession, season: str = "2025-26"):
    """Загружает игроков и их статистику из NBA API

    Использует LeagueDashPlayerStats endpoint для получения агрегированной
    статистики всех игроков за сезон.
    """
    print(f"Загрузка статистики игроков сезона {season}...")

    try:
        await asyncio.sleep(1.0)
        stats = leaguedashplayerstats.LeagueDashPlayerStats(
            season=season,
            season_type_all_star="Regular Season",
            per_mode_detailed="PerGame",
        )
        data = stats.get_dict()
    except Exception as e:
        print(f"Ошибка при загрузке статистики игроков: {type(e).__name__}: {e}")
        return

    result_sets = data.get("resultSets", [])
    if not result_sets:
        print("NBA API вернул пустой response для статистики игроков")
        return

    headers = result_sets[0].get("headers", [])
    rows = result_sets[0].get("rowSet", [])
    print(f"NBA API вернул {len(rows)} записей игроков")

    if not rows:
        print("Нет данных об игроках")
        return

    count_new = 0
    count_updated = 0

    for row in rows:
        player_data = dict(zip(headers, row))

        player_id = player_data.get("PLAYER_ID")
        if not player_id:
            continue

        team_abbr = player_data.get("TEAM_ABBREVIATION", "UNK")

        position = "N/A"
        jersey = None

        games_played = int(player_data.get("GP", 0))
        if games_played == 0:
            continue

        try:
            pts = float(player_data.get("PTS", 0))
            reb = float(player_data.get("REB", 0))
            ast = float(player_data.get("AST", 0))
            stl = float(player_data.get("STL", 0))
            blk = float(player_data.get("BLK", 0))
            fg_pct = float(player_data.get("FG_PCT", 0)) if player_data.get("FG_PCT") else 0.0
            fg3_pct = float(player_data.get("FG3_PCT", 0)) if player_data.get("FG3_PCT") else 0.0
            ft_pct = float(player_data.get("FT_PCT", 0)) if player_data.get("FT_PCT") else 0.0
            mins = float(player_data.get("MIN", 0)) if player_data.get("MIN") else 0.0
        except (ValueError, TypeError):
            continue

        name = player_data.get("PLAYER_NAME", "Unknown")

        existing = await db.execute(select(Player).where(Player.nba_id == int(player_id)))
        player = existing.scalar_one_or_none()

        if not player:
            db.add(Player(
                nba_id=int(player_id),
                name=name,
                team_abbr=team_abbr,
                position=position,
                jersey_number=jersey,
                games_played=games_played,
                pts=pts,
                reb=reb,
                ast=ast,
                stl=stl,
                blk=blk,
                fg_pct=fg_pct,
                fg3_pct=fg3_pct,
                ft_pct=ft_pct,
                mins=mins,
                recent_games=games_played,
            ))
            count_new += 1
        else:
            player.team_abbr = team_abbr
            # position / jersey_number НЕ трогаем: LeagueDashPlayerStats их не
            # отдаёт (position здесь всегда "N/A"). Эти поля наполняются
            # отдельно через backfill_positions.py — перезаписывать нельзя.
            player.games_played = games_played
            player.pts = pts
            player.reb = reb
            player.ast = ast
            player.stl = stl
            player.blk = blk
            player.fg_pct = fg_pct
            player.fg3_pct = fg3_pct
            player.ft_pct = ft_pct
            player.mins = mins
            player.recent_games = games_played
            count_updated += 1

    await db.commit()
    print(f"Игроки синхронизированы: {count_new} новых, {count_updated} обновлено")