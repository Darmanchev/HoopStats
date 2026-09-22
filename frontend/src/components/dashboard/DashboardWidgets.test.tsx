import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { LiveGame, Player, PlayerGameStat, Team, UpcomingGame } from "../../types";
import FeaturedGameWidget from "./FeaturedGameWidget";
import LiveGameStatsWidget from "./LiveGameStatsWidget";
import StandingsWidget from "./StandingsWidget";
import TeamEfficiencyChart from "./TeamEfficiencyChart";
import TopPlayerWidget from "./TopPlayerWidget";
import UpcomingGamesWidget from "./UpcomingGamesWidget";

const bos: Team = {
  abbr: "BOS",
  city: "Boston",
  name: "Celtics",
  record: "60-22",
  conference: "East",
  conferenceRank: 1,
  lastTen: "8-2",
  streak: "W3",
  stats: { teamAbbr: "BOS", form: ["W", "W"], lastScores: [100, 110, 120] },
};

const lal: Team = {
  abbr: "LAL",
  city: "Los Angeles",
  name: "Lakers",
  record: "50-32",
  conference: "West",
  conferenceRank: 2,
  lastTen: "7-3",
  streak: "W1",
  stats: { teamAbbr: "LAL", form: ["W", "L"], lastScores: [105, 115] },
};

const teams = { BOS: bos, LAL: lal };

const scheduledGame: LiveGame = {
  id: "scheduled-1",
  team1: "BOS",
  team2: "LAL",
  isToday: true,
  date: "2026-09-21",
  time: "7:30 PM ET",
  venue: "TD Garden",
  seasonType: "regular",
  season: "2026-27",
  win1: 60,
  prediction: "BOS",
  status: "scheduled",
  statusText: "7:30 PM ET",
  period: null,
  clock: null,
  score1: null,
  score2: null,
};

const liveGame: LiveGame = {
  ...scheduledGame,
  id: "live-1",
  status: "live",
  statusText: "Q3 4:12",
  period: 3,
  clock: "4:12",
  score1: 78,
  score2: 74,
};

const topPlayer: Player = {
  id: 7,
  nbaId: 777,
  name: "Real Leader",
  teamAbbr: "BOS",
  position: "G",
  jerseyNumber: "7",
  gamesPlayed: 20,
  pts: 31.4,
  reb: 8.2,
  ast: 6.5,
  stl: 1.2,
  blk: 0.8,
  fgPct: 52.5,
  fg3Pct: 39,
  ftPct: 88,
  mins: 36,
  recentGames: 10,
};

const playerStat: PlayerGameStat = {
  nbaId: 777,
  name: "Real Leader",
  teamAbbr: "BOS",
  points: 29,
  rebounds: 10,
  assists: 8,
  steals: 2,
  blocks: 1,
  minutes: 35,
};

describe("dashboard widgets", () => {
  it("never displays a fake score for a scheduled featured game", () => {
    render(
      <FeaturedGameWidget
        game={scheduledGame}
        team1={bos}
        team2={lal}
        onOpen={vi.fn()}
      />,
    );

    expect(screen.getByText("7:30 PM ET")).toBeInTheDocument();
    expect(screen.queryByText("112 - 108")).not.toBeInTheDocument();
  });

  it("displays the current score and clock for a live featured game", () => {
    render(
      <FeaturedGameWidget
        game={liveGame}
        team1={bos}
        team2={lal}
        onOpen={vi.fn()}
      />,
    );

    expect(screen.getByText("78 - 74")).toBeInTheDocument();
    expect(screen.getByText(/Q3/)).toBeInTheDocument();
  });

  it("renders a truthful live-stats empty state", () => {
    render(<LiveGameStatsWidget game={null} players={[]} />);
    expect(screen.getByText("No live box score available")).toBeInTheDocument();
  });

  it("orders live player rows by points", () => {
    const lowerScorer = { ...playerStat, nbaId: 888, name: "Second Player", points: 12 };
    render(<LiveGameStatsWidget game={liveGame} players={[lowerScorer, playerStat]} />);

    const rows = screen.getAllByRole("row").slice(1);
    expect(within(rows[0]).getByText("Real Leader")).toBeInTheDocument();
    expect(within(rows[0]).getByText("29")).toBeInTheDocument();
  });

  it("invokes preview navigation with the game id", async () => {
    const onPreview = vi.fn();
    render(
      <UpcomingGamesWidget
        games={[scheduledGame as UpcomingGame]}
        teams={teams}
        onPreview={onPreview}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Preview" }));
    expect(onPreview).toHaveBeenCalledWith(scheduledGame.id);
  });

  it("renders real top-player values and opens the profile", async () => {
    const onOpen = vi.fn();
    render(<TopPlayerWidget player={topPlayer} onOpen={onOpen} />);

    expect(screen.getByText("Real Leader")).toBeInTheDocument();
    expect(screen.getByText("31.4")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Real Leader" })).toHaveAttribute(
      "src",
      expect.stringContaining("777.png"),
    );
    await userEvent.click(screen.getByRole("button", { name: "View Profile" }));
    expect(onOpen).toHaveBeenCalledWith(topPlayer.id);
  });

  it("filters standings by conference", async () => {
    render(<StandingsWidget teams={teams} />);

    expect(screen.getByText("Lakers")).toBeInTheDocument();
    expect(screen.queryByText("Celtics")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "East" }));
    expect(screen.getByText("Celtics")).toBeInTheDocument();
    expect(screen.queryByText("Lakers")).not.toBeInTheDocument();
  });

  it("calculates efficiency average from the selected team's scores", async () => {
    const onSelect = vi.fn();
    const onOpen = vi.fn();
    render(
      <TeamEfficiencyChart
        teams={teams}
        selectedAbbr="BOS"
        onSelect={onSelect}
        onOpen={onOpen}
      />,
    );

    expect(screen.getByText("110.0")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "View Data" }));
    expect(onOpen).toHaveBeenCalledWith("BOS");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Team" }), "LAL");
    expect(onSelect).toHaveBeenCalledWith("LAL");
  });
});
