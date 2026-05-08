// Команда (из TEAMS)
export interface Team {
  abbr: string;
  name: string;
  city: string;
  color: string;
  accent: string;
  record: string;
}

// Травма игрока (из TEAM_DETAILS.injuries)
export interface Injury {
  name: string;
  pos: string;
  injury: string;
  status: "Out" | "Doubtful" | "Questionable" | "Day-to-Day";
}

// Детали команды (из TEAM_DETAILS)
export interface TeamDetails {
  form: ("W" | "L")[];
  lastScores: number[];
  injuries: Injury[];
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
  dateRaw: string;
  time: string;
  venue: string;
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
  dateRaw: string;
  score1: number;
  score2: number;
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
