import type {
  Injury,
  LiveGame,
  PastGame,
  Player,
  PlayerDetail,
  PlayerGameStat,
  Team,
  TeamStats,
  UpcomingGame,
} from "../types";
import { cachedRequest } from "./requestCache";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_MEMORY_CACHE_MS = 30_000;

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

export function getUpcomingGames(): Promise<UpcomingGame[]> {
  return cachedRequest("games:upcoming", API_MEMORY_CACHE_MS, () =>
    fetcher("/games/upcoming"),
  );
}

export function getTodayGames(): Promise<LiveGame[]> {
  return cachedRequest("games:today", API_MEMORY_CACHE_MS, () =>
    fetcher("/games/today"),
  );
}

export async function getPastGames(season?: string): Promise<PastGame[]> {
  const pageSize = 250;
  const games: PastGame[] = [];

  for (let skip = 0; ; skip += pageSize) {
    const qs = new URLSearchParams({
      skip: String(skip),
      limit: String(pageSize),
    });
    if (season) qs.set("season", season);

    const page = await fetcher<PastGame[]>(`/games/past?${qs.toString()}`);
    games.push(...page);
    if (page.length < pageSize) return games;
  }
}

export async function getSeasons(): Promise<string[]> {
  return fetcher("/games/seasons");
}

export async function getMatch(id: string): Promise<LiveGame> {
  return fetcher(`/games/${id}`);
}

export function getTeams(): Promise<Record<string, Team>> {
  return cachedRequest("teams", API_MEMORY_CACHE_MS, () =>
    fetcher<Team[]>("/teams/").then((list) =>
      Object.fromEntries(list.map((team) => [team.abbr, team])),
    ),
  );
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
  season?: string;
}): Promise<Player[]> {
  const qs = new URLSearchParams();
  if (params?.skip !== undefined) qs.set("skip", String(params.skip));
  if (params?.limit !== undefined) qs.set("limit", String(params.limit));
  if (params?.sort_by) qs.set("sort_by", params.sort_by);
  if (params?.team) qs.set("team", params.team);
  if (params?.position) qs.set("position", params.position);
  if (params?.min_games !== undefined) qs.set("min_games", String(params.min_games));
  if (params?.season) qs.set("season", params.season);
  const query = qs.toString();
  return fetcher(`/players/${query ? `?${query}` : ""}`);
}

export function getPlayerSeasons(): Promise<string[]> {
  return fetcher("/players/seasons");
}

export async function getPlayer(
  id: number,
  season?: string,
): Promise<PlayerDetail> {
  const query = season ? `?season=${encodeURIComponent(season)}` : "";
  return fetcher(`/players/${id}${query}`);
}

export interface EloEntry {
  teamAbbr: string;
  elo: number;
}

export async function getElo(): Promise<EloEntry[]> {
  return fetcher("/analytics/elo");
}

export function getLeaders(): Promise<Record<string, Player[]>> {
  return cachedRequest("analytics:leaders", API_MEMORY_CACHE_MS, () =>
    fetcher("/analytics/leaders"),
  );
}

export function getBoxScore(gameId: string): Promise<PlayerGameStat[]> {
  return cachedRequest(`game:${gameId}:boxscore`, API_MEMORY_CACHE_MS, () =>
    fetcher(`/games/${gameId}/boxscore`),
  );
}
