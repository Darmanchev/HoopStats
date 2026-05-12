import type {
  HoopData,
  UpcomingGame,
  PastGame,
  Team,
  TeamDetails,
  Injury,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// базовая функция для всех запросов
async function fetcher<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`);

  if (!response.ok) {
    throw new Error(`Error ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

// ── Матчи ──────────────────────────────────────────

// все предстоящие матчи
export async function getUpcomingGames(): Promise<UpcomingGame[]> {
  return fetcher("/games/upcoming");
}

// матчи сегодня
export async function getTodayGames(): Promise<UpcomingGame[]> {
  return fetcher("/games/today");
}

// прошедшие матчи
export async function getPastGames(): Promise<PastGame[]> {
  return fetcher("/games/past");
}

// один матч по id
export async function getMatch(id: string): Promise<UpcomingGame> {
  return fetcher(`/games/${id}`);
}

// ── Команды ────────────────────────────────────────

// все команды
export async function getTeams(): Promise<Record<string, Team>> {
  const list = await fetcher<(Team & { abbr: string })[]>("/teams");
  return Object.fromEntries(list.map((t) => [t.abbr, t]));
}

// --- Injuries

export async function getInjuries(): Promise<Injury[]> {
  return fetcher("/injuries/");
}

export async function getTeamInjuries(team_abbr: string): Promise<Injury[]> {
  return fetcher(`/injuries/${team_abbr}`);
}
