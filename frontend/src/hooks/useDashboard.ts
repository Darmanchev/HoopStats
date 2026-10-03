import { useCallback, useEffect, useRef, useState } from "react";

import {
  getBoxScore,
  getDashboardSeason,
  getSyncStatus,
  getLeaders,
  getTeams,
  getTodayGames,
  getUpcomingGames,
} from "../lib/api";
import type { DashboardSeasonData, SyncSourceStatus } from "../lib/api";
import type {
  LiveGame,
  Player,
  PlayerGameStat,
  Team,
  UpcomingGame,
} from "../types";

const DEFAULT_REFRESH_MS = 300_000;

type DashboardResource = "teams" | "upcoming" | "today" | "leaders" | "boxScore" | "seasonData" | "sourceStatus";

export type DashboardErrors = Partial<Record<DashboardResource, string>>;

interface DashboardData {
  teams: Record<string, Team>;
  upcoming: UpcomingGame[];
  today: LiveGame[];
  leaders: Record<string, Player[]>;
}

function gameTimestamp(game: LiveGame): number {
  const parsed = Date.parse(
    game.startTime ?? `${game.date}T${game.time || "00:00"}`,
  );
  return Number.isNaN(parsed) ? 0 : parsed;
}

function selectLatestFinalGame(today: LiveGame[]): LiveGame | null {
  return [...today]
    .filter((game) => game.status === "final")
    .sort((left, right) => gameTimestamp(right) - gameTimestamp(left))[0] ?? null;
}

function errorMessage(reason: unknown): string {
  if (reason instanceof Error) return reason.message;
  if (typeof reason === "object" && reason !== null && "message" in reason) {
    return String(reason.message);
  }
  return "Unable to load data";
}

function selectFeaturedGame(
  today: LiveGame[],
  upcoming: UpcomingGame[],
): LiveGame | UpcomingGame | null {
  const live = today.find((game) => game.status === "live");
  if (live) return live;

  const scheduledToday = today.find((game) => game.status === "scheduled");
  if (scheduledToday) return scheduledToday;

  if (upcoming.length > 0) return upcoming[0];

  return selectLatestFinalGame(today);
}

function supportsBoxScore(
  game: LiveGame | UpcomingGame | null,
): game is LiveGame {
  return game !== null && "status" in game && (
    game.status === "live" || game.status === "final"
  );
}

function selectBoxScoreGame(today: LiveGame[]): LiveGame | null {
  const live = today.find((game) => game.status === "live");
  if (live) return live;

  return selectLatestFinalGame(today);
}

export function useDashboard() {
  const [selectedSeason, setSelectedSeason] = useState<string | undefined>();
  const [seasonData, setSeasonData] = useState<{ key: string | undefined; data: DashboardSeasonData } | null>(null);
  const [sourceStatus, setSourceStatus] = useState<Record<string, SyncSourceStatus>>({});
  const requestRef = useRef(0);
  const [teams, setTeams] = useState<Record<string, Team>>({});
  const [upcoming, setUpcoming] = useState<UpcomingGame[]>([]);
  const [today, setToday] = useState<LiveGame[]>([]);
  const [leaders, setLeaders] = useState<Record<string, Player[]>>({});
  const [featuredGame, setFeaturedGame] = useState<LiveGame | UpcomingGame | null>(null);
  const [boxScoreGame, setBoxScoreGame] = useState<LiveGame | null>(null);
  const [boxScore, setBoxScore] = useState<PlayerGameStat[]>([]);
  const [initialLoading, setInitialLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errors, setErrors] = useState<DashboardErrors>({});
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const mountedRef = useRef(false);
  const loadedRef = useRef(false);
  const boxScoreRef = useRef<{ gameId: string | null; players: PlayerGameStat[] }>({
    gameId: null,
    players: [],
  });
  const dataRef = useRef<DashboardData>({
    teams: {},
    upcoming: [],
    today: [],
    leaders: {},
  });

  const refresh = useCallback(async () => {
    const requestId = ++requestRef.current;
    const isInitialLoad = !loadedRef.current;
    if (!isInitialLoad && mountedRef.current) setRefreshing(true);

    const results = await Promise.allSettled([
      getTeams(),
      getUpcomingGames(),
      getTodayGames(),
      getLeaders(selectedSeason),
      getDashboardSeason(selectedSeason),
      getSyncStatus(),
    ] as const);

    if (!mountedRef.current || requestId !== requestRef.current) return;

    const nextData = { ...dataRef.current };
    const nextErrors: DashboardErrors = {};
    const [teamsResult, upcomingResult, todayResult, leadersResult] = results;
    const primaryRefreshSucceeded = results.slice(0, 4).some((result) => result.status === "fulfilled");
    const [seasonResult, statusResult] = results.slice(4);
    if (seasonResult.status === "fulfilled") {
      setSeasonData({ key: selectedSeason, data: seasonResult.value as DashboardSeasonData });
    } else {
      nextErrors.seasonData = errorMessage(seasonResult.reason);
    }
    if (statusResult.status === "fulfilled") {
      setSourceStatus(statusResult.value as Record<string, SyncSourceStatus>);
    } else {
      nextErrors.sourceStatus = errorMessage(statusResult.reason);
    }

    if (teamsResult.status === "fulfilled") {
      nextData.teams = teamsResult.value;
      setTeams(teamsResult.value);
    } else {
      nextErrors.teams = errorMessage(teamsResult.reason);
    }

    if (upcomingResult.status === "fulfilled") {
      nextData.upcoming = upcomingResult.value;
      setUpcoming(upcomingResult.value);
    } else {
      nextErrors.upcoming = errorMessage(upcomingResult.reason);
    }

    if (todayResult.status === "fulfilled") {
      nextData.today = todayResult.value;
      setToday(todayResult.value);
    } else {
      nextErrors.today = errorMessage(todayResult.reason);
    }

    if (leadersResult.status === "fulfilled") {
      nextData.leaders = leadersResult.value;
      setLeaders(leadersResult.value);
    } else {
      nextErrors.leaders = errorMessage(leadersResult.reason);
    }

    dataRef.current = nextData;
    const nextFeaturedGame = selectFeaturedGame(nextData.today, nextData.upcoming);
    setFeaturedGame(nextFeaturedGame);
    const nextBoxScoreGame = selectBoxScoreGame(nextData.today);
    setBoxScoreGame(nextBoxScoreGame);

    if (supportsBoxScore(nextBoxScoreGame)) {
      if (boxScoreRef.current.gameId !== nextBoxScoreGame.id) {
        boxScoreRef.current = { gameId: nextBoxScoreGame.id, players: [] };
        setBoxScore([]);
      }
      try {
        const stats = await getBoxScore(nextBoxScoreGame.id);
        if (!mountedRef.current || requestId !== requestRef.current) return;
        boxScoreRef.current = { gameId: nextBoxScoreGame.id, players: stats };
        setBoxScore(stats);
      } catch (reason) {
        nextErrors.boxScore = errorMessage(reason);
      }
    } else {
      boxScoreRef.current = { gameId: null, players: [] };
      setBoxScore([]);
    }

    if (!mountedRef.current || requestId !== requestRef.current) return;
    setErrors(nextErrors);
    if (primaryRefreshSucceeded) setLastUpdated(new Date());
    loadedRef.current = true;
    setInitialLoading(false);
    setRefreshing(false);
  }, [selectedSeason]);

  useEffect(() => {
    mountedRef.current = true;
    void Promise.resolve().then(() => {
      if (mountedRef.current) void refresh();
    });

    const configuredInterval = Number(
      import.meta.env.VITE_DASHBOARD_REFRESH_MS ?? DEFAULT_REFRESH_MS,
    );
    const refreshInterval = Number.isFinite(configuredInterval) && configuredInterval > 0
      ? configuredInterval
      : DEFAULT_REFRESH_MS;
    const intervalId = window.setInterval(() => {
      void refresh();
    }, refreshInterval);

    return () => {
      mountedRef.current = false;
      window.clearInterval(intervalId);
    };
  }, [refresh]);

  return {
    selectedSeason,
    setSelectedSeason,
    seasonData: seasonData && seasonData.key === selectedSeason ? seasonData.data : null,
    sourceStatus,
    importedSeasons: seasonData?.data.seasons ?? [],
    teams,
    upcoming,
    today,
    leaders,
    featuredGame,
    boxScoreGame,
    boxScore,
    initialLoading,
    refreshing,
    errors,
    lastUpdated,
    refresh,
  };
}
