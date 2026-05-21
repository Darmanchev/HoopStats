// Команда (из TEAMS)
export interface Team {
  abbr: string;
  name: string;
  city: string;
  color: string;
  accent: string;
  record: string;
}

// Травма игрока (из API /injuries)
export interface Injury {
  id: string;
  teamAbbr: string;
  playerName: string;
  position: string;
  injury: string;
  status: "Out" | "Doubtful" | "Questionable" | "Day-to-Day";
}

// Детали команды (из TEAM_DETAILS)
export interface TeamDetails {
  form: ("W" | "L")[];
  lastScores: number[];
  injuries: Injury[];
}

export interface TeamStats {
  teamAbbr: string;
  form: ("W" | "L")[];
  lastScores: number[];
}

// Фактор прогноза (из UPCOMING.factors)
export interface Factor {
  label: string;
  val1: number;
  val2: number;
  invert?: boolean;
}

// Предстоящий матч (из UPCOMING)
export interface UpcomingGame {
  id: string;
  team1: string;
  team2: string;
  isToday: boolean;
  date: string;
  time: string;
  venue: string;
  seasonType: "regular" | "playoffs";
  season: string;
  win1: number;
  prediction: string;
  factors: Factor[];
}

// Прошедший матч (из PAST)
export interface PastGame {
  id: string;
  team1: string;
  team2: string;
  date: string;
  seasonType: "regular" | "playoffs";
  season: string;
  score1: number;
  score2: number;
}

export interface Player {
  id: number;
  nbaId: number;
  name: string;
  teamAbbr: string;
  position: string;
  jerseyNumber: string | null;
  gamesPlayed: number;
  pts: number;
  reb: number;
  ast: number;
  stl: number;
  blk: number;
  fgPct: number;
  fg3Pct: number;
  ftPct: number;
  mins: number;
  recentGames: number;
}

export interface PlayerDetail extends Player {
  teamName: string | null;
  teamCity: string | null;
  teamColor: string | null;
  teamAccent: string | null;
}

// Объединённый тип для Schedule (где матч может быть любым)
export type Game = UpcomingGame | PastGame;

// Все данные (структура HOOPDATA)
export interface HoopData {
  TEAMS: Record<string, Team>;
  TEAM_DETAILS: Record<string, TeamDetails>;
  UPCOMING: UpcomingGame[];
  PAST: PastGame[];
}
