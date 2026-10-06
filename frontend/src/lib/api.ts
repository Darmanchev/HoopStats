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

export function getTeams(season?: string): Promise<Record<string, Team>> {
  const query = season ? `?season=${encodeURIComponent(season)}` : "";
  return cachedRequest(season ? `teams:${season}` : "teams", API_MEMORY_CACHE_MS, () =>
    fetcher<Team[]>(`/teams/${query}`).then((list) =>
      Object.fromEntries(list.map((team) => [team.abbr, team])),
    ),
  );
}

export function getTeamSeasons(): Promise<string[]> {
  return fetcher("/teams/seasons");
}

export async function getTeamStats(abbr: string, season?: string): Promise<TeamStats> {
  const query = season ? `?season=${encodeURIComponent(season)}` : "";
  return fetcher(`/teams/${abbr}/stats${query}`)
}

export async function getInjuries(): Promise<Injury[]> {
  return fetcher("/injuries/");
}

export async function getTeamInjuries(team_abbr: string): Promise<Injury[]> {
  return fetcher(`/injuries/${team_abbr}`);
}

export async function getPlayers(params?: {
  search?: string;
  ids?: string;
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
  if (params?.ids) qs.set("ids", params.ids);
  if (params?.search) qs.set("search", params.search);
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

export async function getElo(season?: string): Promise<EloEntry[]> {
  return fetcher(`/analytics/elo${season ? `?season=${encodeURIComponent(season)}` : ""}`);
}

export function getLeaders(season?: string): Promise<Record<string, Player[]>> {
  const query = season ? `?season=${encodeURIComponent(season)}` : "";
  return cachedRequest(`analytics:leaders:${season ?? "latest"}`, API_MEMORY_CACHE_MS, () =>
    fetcher(`/analytics/leaders${query}`),
  );
}

export interface DashboardSeasonData {
  season: string | null;
  seasons: string[];
  teams: Team[];
  leaders: Record<string, Player[]>;
  teamsAvailable: boolean;
  playersAvailable: boolean;
}

export interface SyncSourceStatus {
  state: "queued" | "running" | "success" | "failed";
  last_attempt?: string;
  last_success?: string;
  started_at?: string | null;
  finished_at?: string | null;
  duration_seconds?: number | null;
  queued_at?: string;
  count?: number | null;
}

export function getDashboardSeason(season?: string): Promise<DashboardSeasonData> {
  return fetcher(`/analytics/dashboard${season ? `?season=${encodeURIComponent(season)}` : ""}`);
}

export async function retrySync(source: string, token: string): Promise<{queued: boolean}> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/analytics/sync-retry`, {
      method: "POST", headers: { "Content-Type": "application/json", "X-Sync-Token": token },
      body: JSON.stringify({source}),
    });
  } catch { throw createApiError(0, "Retry could not be queued"); }
  if (!response.ok) throw createApiError(response.status, `Retry failed (${response.status})`);
  return response.json();
}

export function getSyncStatus(): Promise<Record<string, SyncSourceStatus>> {
  return fetcher("/analytics/sync-status");
}

export function getBoxScore(gameId: string): Promise<PlayerGameStat[]> {
  return cachedRequest(`game:${gameId}:boxscore`, API_MEMORY_CACHE_MS, () =>
    fetcher(`/games/${gameId}/boxscore`),
  );
}

export interface Page<T> { items: T[]; total: number }
export interface ScheduleParams {
  season?: string; season_type?: string; status?: string; team?: string;
  date_from?: string; date_to?: string; weekday?: number; skip?: number; limit?: number;
}
export function getSchedule(params: ScheduleParams): Promise<Page<LiveGame>> {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) if (value !== undefined && value !== "") query.set(key, String(value));
  return fetcher(`/games/?${query}`);
}
export function getScheduleMonths(season?: string): Promise<string[]> {
  return fetcher(`/games/months${season ? `?season=${encodeURIComponent(season)}` : ""}`);
}
export interface SearchEntry { id: string; label: string; url: string }
export type SearchResults = Record<"players" | "teams" | "games", SearchEntry[]>;
export function getSearch(query: string): Promise<SearchResults> {
  return fetcher(`/search?q=${encodeURIComponent(query)}&limit=5`);
}
export interface PlayerLog {
  gameId: string; date: string; teamAbbr: string; opponent: string; homeAway: string;
  result: string | null; points: number; rebounds: number; assists: number; steals: number; blocks: number; minutes: number;
}
export interface PlayerLogs extends Page<PlayerLog> {
  coverage: { identityResolved: boolean; importedGames: number; note: string };
}
export function getPlayerGames(id: number, season?: string, skip = 0): Promise<PlayerLogs> {
  const query = new URLSearchParams({skip:String(skip),limit:"20"});
  if (season) query.set("season", season);
  return fetcher(`/players/${id}/games?${query}`);
}
export interface EvaluationMetrics { accuracy: number; log_loss: number; brier: number; auc: number | null }
export interface EvaluationReport {
  available: boolean; reason?: string; test_season?: string; trained_at?: string; n_train?: number; n_test?: number;
  metrics?: EvaluationMetrics; baselines?: Record<string, EvaluationMetrics>;
  calibration?: { lower: number; upper: number; count: number; predicted: number | null; observed: number | null }[];
  games: { id: string; date: string; team1: string; team2: string; probability: number; actual: number; correct: boolean }[];
  total: number;
  seasons?: string[]; selected_season?: string | null; season_metrics?: EvaluationMetrics | null;
}
export function getModelPerformance(skip = 0, season?: string): Promise<EvaluationReport> {
  return fetcher(`/analytics/model-performance?skip=${skip}&limit=20${season ? `&season=${encodeURIComponent(season)}` : ""}`);
}
