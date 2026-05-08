from sqlalchemy.ext.asyncio import AsyncSession
from .models.team import Team
from .models.game import Game
from .models.injury import Injury
from datetime import date

async def seed(db: AsyncSession):
    teams = [
        Team(abbr="LAL", name="Lakers",   city="Los Angeles",  color="#3B1F6B", accent="#FDB927", record="52-28"),
        Team(abbr="BOS", name="Celtics",  city="Boston",       color="#006532", accent="#9DC535", record="58-22"),
        Team(abbr="GSW", name="Warriors", city="Golden State", color="#1D428A", accent="#FFC72C", record="49-31"),
        Team(abbr="MIA", name="Heat",     city="Miami",        color="#8B0022", accent="#F9A01B", record="44-36"),
        Team(abbr="DEN", name="Nuggets",  city="Denver",       color="#0E2240", accent="#FEC524", record="51-29"),
        Team(abbr="MIL", name="Bucks",    city="Milwaukee",    color="#003313", accent="#A3D55C", record="47-33"),
        Team(abbr="NYK", name="Knicks",   city="New York",     color="#005BA1", accent="#F58426", record="50-30"),
        Team(abbr="OKC", name="Thunder",  city="Oklahoma City",color="#00599C", accent="#EF3B24", record="57-23"),
        Team(abbr="PHX", name="Suns",     city="Phoenix",      color="#1D1160", accent="#E56020", record="43-37"),
        Team(abbr="LAC", name="Clippers", city="Los Angeles",  color="#7B1028", accent="#1168C4", record="46-34"),
    ]

    games = [
        Game(id="g1", team1="LAL", team2="BOS", date=date(2026,4,25), time="7:30 PM ET", venue="Crypto.com Arena",   is_today=True, win1=44, prediction="Boston enters as moderate favorites..."),
        Game(id="g2", team1="GSW", team2="MIA", date=date(2026,4,25), time="10:00 PM ET", venue="Chase Center",      is_today=True, win1=63, prediction="Golden State are heavy favorites..."),
        Game(id="g3", team1="NYK", team2="OKC", date=date(2026,4,25), time="8:00 PM ET", venue="Madison Square Garden", is_today=True, win1=38, prediction="OKC are favored despite the road trip..."),
        Game(id="g4", team1="DEN", team2="MIL", date=date(2026,4,26), time="8:00 PM ET", venue="Ball Arena",         is_today=False, win1=59, prediction="Denver's home court and Nikola Jokić..."),
        Game(id="g5", team1="PHX", team2="LAC", date=date(2026,4,27), time="9:30 PM ET", venue="Footprint Center",   is_today=False, win1=48, prediction="A coin-flip Western Conference matchup..."),
        Game(id="p1", team1="BOS", team2="DEN", date=date(2026,4,22), time="", venue="", is_today=False, score1=121, score2=110),
        Game(id="p2", team1="LAL", team2="PHX", date=date(2026,4,22), time="", venue="", is_today=False, score1=115, score2=108),
        Game(id="p3", team1="GSW", team2="NYK", date=date(2026,4,21), time="", venue="", is_today=False, score1=128, score2=119),
        Game(id="p4", team1="OKC", team2="MIL", date=date(2026,4,21), time="", venue="", is_today=False, score1=118, score2=104),
        Game(id="p5", team1="MIA", team2="LAC", date=date(2026,4,20), time="", venue="", is_today=False, score1=103, score2=97),
    ]

    injuries = [
        Injury(team_abbr="LAL", player_name="Anthony Davis",     position="C",  injury="Right knee soreness",       status="Questionable"),
        Injury(team_abbr="LAL", player_name="Jarred Vanderbilt", position="SF", injury="Left foot stress fracture", status="Out"),
        Injury(team_abbr="BOS", player_name="Kristaps Porzingis",position="C",  injury="Left ankle sprain",         status="Questionable"),
        Injury(team_abbr="GSW", player_name="Stephen Curry",     position="PG", injury="Left hamstring tightness",  status="Day-to-Day"),
        Injury(team_abbr="GSW", player_name="Draymond Green",    position="PF", injury="Back contusion",            status="Questionable"),
        Injury(team_abbr="MIA", player_name="Jimmy Butler",      position="SF", injury="Right knee MCL sprain",     status="Out"),
        Injury(team_abbr="MIA", player_name="Tyler Herro",       position="SG", injury="Groin strain",              status="Doubtful"),
        Injury(team_abbr="NYK", player_name="Julius Randle",     position="PF", injury="Right shoulder subluxation",status="Out"),
        Injury(team_abbr="PHX", player_name="Devin Booker",      position="SG", injury="Left thumb sprain",         status="Questionable"),
        Injury(team_abbr="LAC", player_name="Paul George",       position="SF", injury="Right knee tendinopathy",   status="Day-to-Day"),
    ]

    db.add_all(teams)
    db.add_all(games)
    db.add_all(injuries)
    await db.commit()