import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { LiveGame, Player, Team, UpcomingGame } from "../types";
import { useDashboard } from "../hooks/useDashboard";
import Dashboard from "./Dashboard";

vi.mock("../hooks/useDashboard", () => ({
  useDashboard: vi.fn(),
}));

const teams: Record<string, Team> = {
  BOS: {
    abbr: "BOS",
    city: "Boston",
    name: "Celtics",
    record: "60-22",
    conference: "East",
    conferenceRank: 1,
    stats: { teamAbbr: "BOS", form: ["W"], lastScores: [110, 115] },
  },
  LAL: {
    abbr: "LAL",
    city: "Los Angeles",
    name: "Lakers",
    record: "50-32",
    conference: "West",
    conferenceRank: 2,
  },
};

const upcoming: UpcomingGame = {
  id: "0022500001",
  team1: "BOS",
  team2: "LAL",
  isToday: false,
  date: "2026-09-22",
  time: "7:30 PM ET",
  venue: "TD Garden",
  seasonType: "regular",
  season: "2026-27",
  win1: 55,
  prediction: "BOS",
};

const live: LiveGame = {
  ...upcoming,
  id: "live-1",
  isToday: true,
  status: "live",
  statusText: "Q2 5:00",
  period: 2,
  clock: "5:00",
  score1: 48,
  score2: 45,
};

const player: Player = {
  id: 2544,
  nbaId: 2544,
  name: "League Leader",
  teamAbbr: "LAL",
  position: "F",
  jerseyNumber: "23",
  gamesPlayed: 20,
  pts: 30,
  reb: 8,
  ast: 7,
  stl: 1,
  blk: 1,
  fgPct: 52,
  fg3Pct: 38,
  ftPct: 80,
  mins: 35,
  recentGames: 10,
};

const dashboardData = {
  teams,
  upcoming: [upcoming],
  today: [live],
  leaders: { pts: [player] },
  featuredGame: live,
  boxScoreGame: live,
  boxScore: [],
  initialLoading: false,
  refreshing: false,
  errors: {},
  lastUpdated: new Date("2026-09-21T12:00:00Z"),
  refresh: vi.fn(async () => undefined),
};

function LocationProbe() {
  return <output data-testid="location">{useLocation().pathname}</output>;
}

function renderDashboard() {
  return render(
    <MemoryRouter>
      <Dashboard />
      <LocationProbe />
    </MemoryRouter>,
  );
}

describe("Dashboard", () => {
  beforeEach(() => {
    vi.mocked(useDashboard).mockReturnValue(dashboardData);
  });

  it("navigates dashboard actions to existing routes", async () => {
    renderDashboard();

    await userEvent.click(screen.getByRole("button", { name: "Preview" }));
    expect(screen.getByTestId("location")).toHaveTextContent("/match/0022500001");

    await userEvent.click(screen.getByRole("button", { name: "View Profile" }));
    expect(screen.getByTestId("location")).toHaveTextContent("/players/2544");

    await userEvent.click(screen.getByRole("button", { name: "View Data" }));
    expect(screen.getByTestId("location")).toHaveTextContent("/teams/BOS");
  });

  it("keeps widgets visible and warns when refresh data is incomplete", () => {
    vi.mocked(useDashboard).mockReturnValue({
      ...dashboardData,
      errors: { today: "offline" },
    });

    renderDashboard();

    expect(screen.getByText("Upcoming Games")).toBeInTheDocument();
    expect(screen.getByText(/some data could not be refreshed/i)).toBeInTheDocument();
  });

  it("shows refresh status without hiding existing widgets", () => {
    vi.mocked(useDashboard).mockReturnValue({ ...dashboardData, refreshing: true });

    renderDashboard();

    expect(screen.getByText("Updating…")).toBeInTheDocument();
    expect(screen.getByText("Upcoming Games")).toBeInTheDocument();
  });
});
