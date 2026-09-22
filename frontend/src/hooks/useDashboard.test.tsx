import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { LiveGame, Player, Team, UpcomingGame } from "../types";
import {
  getBoxScore,
  getLeaders,
  getTeams,
  getTodayGames,
  getUpcomingGames,
} from "../lib/api";
import { useDashboard } from "./useDashboard";

vi.mock("../lib/api", () => ({
  getBoxScore: vi.fn(),
  getLeaders: vi.fn(),
  getTeams: vi.fn(),
  getTodayGames: vi.fn(),
  getUpcomingGames: vi.fn(),
}));

const team: Team = {
  abbr: "BOS",
  name: "Celtics",
  city: "Boston",
  record: "60-22",
};

const upcomingGame: UpcomingGame = {
  id: "upcoming-1",
  team1: "BOS",
  team2: "NYK",
  isToday: false,
  date: "2026-09-22",
  time: "19:30",
  venue: "TD Garden",
  seasonType: "regular",
  season: "2026-27",
  win1: 55,
  prediction: "BOS",
};

const liveGame: LiveGame = {
  ...upcomingGame,
  id: "live-1",
  isToday: true,
  status: "live",
  statusText: "Q3 04:12",
  period: 3,
  clock: "PT04M12S",
  score1: 78,
  score2: 75,
};

const leader: Player = {
  id: 1,
  nbaId: 101,
  name: "Test Player",
  teamAbbr: "BOS",
  position: "F",
  jerseyNumber: "0",
  gamesPlayed: 10,
  pts: 25,
  reb: 8,
  ast: 5,
  stl: 1,
  blk: 1,
  fgPct: 50,
  fg3Pct: 40,
  ftPct: 85,
  mins: 34,
  recentGames: 10,
};

const mockedGetTeams = vi.mocked(getTeams);
const mockedGetUpcomingGames = vi.mocked(getUpcomingGames);
const mockedGetTodayGames = vi.mocked(getTodayGames);
const mockedGetLeaders = vi.mocked(getLeaders);
const mockedGetBoxScore = vi.mocked(getBoxScore);

function mockSuccessfulRefresh() {
  mockedGetTeams.mockResolvedValue({ BOS: team });
  mockedGetUpcomingGames.mockResolvedValue([upcomingGame]);
  mockedGetTodayGames.mockResolvedValue([liveGame]);
  mockedGetLeaders.mockResolvedValue({ points: [leader] });
  mockedGetBoxScore.mockResolvedValue([]);
}

describe("useDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSuccessfulRefresh();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("loads immediately and refreshes after five minutes", async () => {
    vi.useFakeTimers();
    renderHook(() => useDashboard());

    await act(async () => {
      await Promise.resolve();
    });
    expect(mockedGetTodayGames).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(300_000);
    });
    expect(mockedGetTodayGames).toHaveBeenCalledTimes(2);
  });

  it("keeps previous teams when only the teams refresh fails", async () => {
    const { result } = renderHook(() => useDashboard());
    await waitFor(() => expect(result.current.teams.BOS).toBeDefined());

    mockedGetTeams.mockRejectedValueOnce(new Error("offline"));
    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.teams.BOS).toEqual(team);
    expect(result.current.errors.teams).toBe("offline");
    expect(result.current.today).toEqual([liveGame]);
  });

  it("keeps the previous update time when every primary refresh fails", async () => {
    const { result } = renderHook(() => useDashboard());
    await waitFor(() => expect(result.current.lastUpdated).not.toBeNull());
    const successfulUpdate = result.current.lastUpdated;

    mockedGetTeams.mockRejectedValueOnce(new Error("offline"));
    mockedGetUpcomingGames.mockRejectedValueOnce(new Error("offline"));
    mockedGetTodayGames.mockRejectedValueOnce(new Error("offline"));
    mockedGetLeaders.mockRejectedValueOnce(new Error("offline"));
    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.lastUpdated).toBe(successfulUpdate);
  });

  it("selects a live featured game and loads its box score", async () => {
    const { result } = renderHook(() => useDashboard());

    await waitFor(() => expect(result.current.initialLoading).toBe(false));

    expect(result.current.featuredGame?.id).toBe(liveGame.id);
    expect(mockedGetBoxScore).toHaveBeenCalledWith(liveGame.id);
  });

  it("loads the latest final box score even when an upcoming game is featured", async () => {
    const finalGame: LiveGame = {
      ...liveGame,
      id: "final-1",
      status: "final",
      statusText: "Final",
      clock: null,
      score1: 110,
      score2: 104,
    };
    mockedGetTodayGames.mockResolvedValueOnce([finalGame]);
    const { result } = renderHook(() => useDashboard());

    await waitFor(() => expect(result.current.initialLoading).toBe(false));

    expect(result.current.featuredGame?.id).toBe(upcomingGame.id);
    expect(result.current.boxScoreGame?.id).toBe(finalGame.id);
    expect(mockedGetBoxScore).toHaveBeenCalledWith(finalGame.id);
  });

  it("selects the most recent final game by normalized start time", async () => {
    const olderFinal: LiveGame = {
      ...liveGame,
      id: "final-older",
      status: "final",
      statusText: "Final",
      time: "Final",
      startTime: "2026-09-21T18:00:00Z",
    };
    const newerFinal: LiveGame = {
      ...olderFinal,
      id: "final-newer",
      startTime: "2026-09-21T22:00:00Z",
    };
    mockedGetUpcomingGames.mockResolvedValueOnce([]);
    mockedGetTodayGames.mockResolvedValueOnce([olderFinal, newerFinal]);
    const { result } = renderHook(() => useDashboard());

    await waitFor(() => expect(result.current.initialLoading).toBe(false));

    expect(result.current.featuredGame?.id).toBe(newerFinal.id);
    expect(result.current.boxScoreGame?.id).toBe(newerFinal.id);
  });

  it("clears players when a different game's box score fails", async () => {
    const firstRows = [{
      nbaId: 101,
      name: "Test Player",
      teamAbbr: "BOS",
      points: 20,
      rebounds: 5,
      assists: 4,
      steals: 1,
      blocks: 0,
      minutes: 30,
    }];
    mockedGetBoxScore.mockResolvedValueOnce(firstRows);
    const { result } = renderHook(() => useDashboard());
    await waitFor(() => expect(result.current.boxScore).toEqual(firstRows));

    const nextGame = { ...liveGame, id: "live-2" };
    mockedGetTodayGames.mockResolvedValueOnce([nextGame]);
    mockedGetBoxScore.mockRejectedValueOnce(new Error("offline"));
    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.boxScoreGame?.id).toBe(nextGame.id);
    expect(result.current.boxScore).toEqual([]);
    expect(result.current.errors.boxScore).toBe("offline");
  });

  it("clears the refresh timer when unmounted", () => {
    const clearIntervalSpy = vi.spyOn(window, "clearInterval");
    const { unmount } = renderHook(() => useDashboard());

    unmount();

    expect(clearIntervalSpy).toHaveBeenCalled();
  });
});
