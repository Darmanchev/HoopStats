import { useCallback, useEffect, useRef, useState } from "react";

import {
  getBoxScore,
  getLeaders,
  getTeams,
  getTodayGames,
  getUpcomingGames,
} from "../lib/api";
import type {
  LiveGame,
  Player,
  PlayerGameStat,
  Team,
  UpcomingGame,
} from "../types";

const DEFAULT_REFRESH_MS = 300_000;

type DashboardResource = "teams" | "upcoming" | "today" | "leaders" | "boxScore";

export type DashboardErrors = Partial<Record<DashboardResource, string>>;

interface DashboardData {
  teams: Record<string, Team>;
  upcoming: UpcomingGame[];
  today: LiveGame[];
  leaders: Record<string, Player[]>;
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

  return [...today]
    .filter((game) => game.status === "final")
    .sort((left, right) => {
      const leftTime = Date.parse(`${left.date}T${left.time || "00:00"}`);
      const rightTime = Date.parse(`${right.date}T${right.time || "00:00"}`);
      return rightTime - leftTime;
    })[0] ?? null;
}

function supportsBoxScore(
  game: LiveGame | UpcomingGame | null,
): game is LiveGame {
  return game !== null && "status" in game && (
    game.status === "live" || game.status === "final"
  );
}

export function useDashboard() {
  const [teams, setTeams] = useState<Record<string, Team>>({});
  const [upcoming, setUpcoming] = useState<UpcomingGame[]>([]);
  const [today, setToday] = useState<LiveGame[]>([]);
  const [leaders, setLeaders] = useState<Record<string, Player[]>>({});
  const [featuredGame, setFeaturedGame] = useState<LiveGame | UpcomingGame | null>(null);
  const [boxScore, setBoxScore] = useState<PlayerGameStat[]>([]);
  const [initialLoading, setInitialLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errors, setErrors] = useState<DashboardErrors>({});
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const mountedRef = useRef(false);
  const loadedRef = useRef(false);
  const dataRef = useRef<DashboardData>({
    teams: {},
    upcoming: [],
    today: [],
    leaders: {},
  });

  const refresh = useCallback(async () => {
    const isInitialLoad = !loadedRef.current;
    if (!isInitialLoad && mountedRef.current) setRefreshing(true);

    const results = await Promise.allSettled([
      getTeams(),
      getUpcomingGames(),
      getTodayGames(),
      getLeaders(),
    ] as const);

    if (!mountedRef.current) return;

    const nextData = { ...dataRef.current };
    const nextErrors: DashboardErrors = {};
    const [teamsResult, upcomingResult, todayResult, leadersResult] = results;
    const primaryRefreshSucceeded = results.some((result) => result.status === "fulfilled");

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

    if (supportsBoxScore(nextFeaturedGame)) {
      try {
        const stats = await getBoxScore(nextFeaturedGame.id);
        if (!mountedRef.current) return;
        setBoxScore(stats);
      } catch (reason) {
        nextErrors.boxScore = errorMessage(reason);
      }
    } else {
      setBoxScore([]);
    }

    if (!mountedRef.current) return;
    setErrors(nextErrors);
    if (primaryRefreshSucceeded) setLastUpdated(new Date());
    loadedRef.current = true;
    setInitialLoading(false);
    setRefreshing(false);
  }, []);

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
    teams,
    upcoming,
    today,
    leaders,
    featuredGame,
    boxScore,
    initialLoading,
    refreshing,
    errors,
    lastUpdated,
    refresh,
  };
}
