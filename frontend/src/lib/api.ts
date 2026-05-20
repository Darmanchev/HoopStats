import type { TeamStats, UpcomingGame, PastGame, Team, Injury, Player, PlayerDetail } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface ApiError {
  status: number;
  message: string;
  name: "ApiError";
}

function createApiError(status: number, message: string): ApiError {
  return { status, message, name: "ApiError" };
}

async function fetcher<T>(endpoint: string): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${BASE_URL}${endpoint}`);
  } catch {
    throw createApiError(0, "Network error — check your connection");
  }

  if (!response.ok) {
    throw createApiError(
      response.status,
      `Error ${response.status}: ${response.statusText}`
    );
  }

  return response.json();
}

export async function getUpcomingGames(): Promise<UpcomingGame[]> {
  return fetcher("/games/upcoming");
}

export async function getTodayGames(): Promise<UpcomingGame[]> {
  return fetcher("/games/today");
}

export async function getPastGames(season?: string): Promise<PastGame[]> {
  const qs = new URLSearchParams({ limit: "5000" });
  if (season) qs.set("season", season);
  return fetcher(`/games/past?${qs.toString()}`);
}

export async function getSeasons(): Promise<string[]> {
  return fetcher("/games/seasons");
}

export async function getMatch(id: string): Promise<UpcomingGame> {
  return fetcher(`/games/${id}`);
}

export async function getTeams(): Promise<Record<string, Team>> {
  const list = await fetcher<(Team & { abbr: string })[]>("/teams/");
  return Object.fromEntries(list.map((t) => [t.abbr, t]));
}

export async function getTeamStats(abbr: string): Promise<TeamStats> {
  return fetcher(`/teams/${abbr}/stats`)
}

export async function getInjuries(): Promise<Injury[]> {
  return fetcher("/injuries/");
}

export async function getTeamInjuries(team_abbr: string): Promise<Injury[]> {
  return fetcher(`/injuries/${team_abbr}`);
}

export async function getPlayers(params?: {
  skip?: number;
  limit?: number;
  sort_by?: string;
  team?: string;
  position?: string;
  min_games?: number;
}): Promise<Player[]> {
  const qs = new URLSearchParams();
  if (params?.skip !== undefined) qs.set("skip", String(params.skip));
  if (params?.limit !== undefined) qs.set("limit", String(params.limit));
  if (params?.sort_by) qs.set("sort_by", params.sort_by);
  if (params?.team) qs.set("team", params.team);
  if (params?.position) qs.set("position", params.position);
  if (params?.min_games !== undefined) qs.set("min_games", String(params.min_games));
  const query = qs.toString();
  return fetcher(`/players/${query ? `?${query}` : ""}`);
}

export async function getPlayer(id: number): Promise<PlayerDetail> {
  return fetcher(`/players/${id}`);
}
