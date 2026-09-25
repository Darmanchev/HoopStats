import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  MemoryRouter,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  getPlayer,
  getPlayerSeasons,
  getPlayers,
  getTeams,
} from "../lib/api";
import type { Player, PlayerDetail } from "../types";
import PlayerDetailPage from "./PlayerDetail";
import Players from "./Players";


vi.mock("../lib/api", () => ({
  getPlayer: vi.fn(),
  getPlayerSeasons: vi.fn(),
  getPlayers: vi.fn(),
  getTeams: vi.fn(),
}));


const player: Player = {
  id: 1,
  nbaId: 201939,
  balldontlieId: 115,
  apiNbaId: 417,
  season: "2025-26",
  name: "Stephen Curry",
  teamAbbr: "GSW",
  position: "G",
  jerseyNumber: "30",
  gamesPlayed: 79,
  pts: 26.4,
  reb: 4.5,
  ast: 6.1,
  stl: 1,
  blk: 0.4,
  fgPct: 0.47,
  fg3Pct: 0.41,
  ftPct: 0.92,
  mins: 33.2,
  recentGames: 10,
};


function LocationProbe() {
  const location = useLocation();
  return <output data-testid="location">{location.pathname}{location.search}</output>;
}


function renderPlayers(initialEntry = "/players") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/players" element={<Players />} />
        <Route path="/players/:id" element={<PlayerDetailPage />} />
      </Routes>
      <LocationProbe />
    </MemoryRouter>,
  );
}


describe("Players season selection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getTeams).mockResolvedValue({
      GSW: {
        abbr: "GSW",
        city: "Golden State",
        name: "Warriors",
        record: "0-0",
      },
    });
    vi.mocked(getPlayers).mockResolvedValue([player]);
    vi.mocked(getPlayerSeasons).mockResolvedValue(["2025-26", "2024-25"]);
    vi.mocked(getPlayer).mockResolvedValue({
      ...player,
      teamName: "Warriors",
      teamCity: "Golden State",
    } satisfies PlayerDetail);
  });

  it("defaults to the newest imported player season", async () => {
    renderPlayers();

    await waitFor(() =>
      expect(getPlayers).toHaveBeenCalledWith(
        expect.objectContaining({ season: "2025-26" }),
      ),
    );
    expect(screen.getByRole("combobox", { name: /season/i })).toHaveValue(
      "2025-26",
    );
    expect(screen.getByTestId("location")).toHaveTextContent(
      "/players?season=2025-26",
    );
  });

  it("uses an explicit season and updates the URL when selection changes", async () => {
    renderPlayers("/players?season=2024-25");

    const select = await screen.findByRole("combobox", { name: /season/i });
    expect(select).toHaveValue("2024-25");
    await waitFor(() =>
      expect(getPlayers).toHaveBeenCalledWith(
        expect.objectContaining({ season: "2024-25" }),
      ),
    );

    await userEvent.selectOptions(select, "2025-26");

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/players?season=2025-26",
    );
    await waitFor(() =>
      expect(getPlayers).toHaveBeenLastCalledWith(
        expect.objectContaining({ season: "2025-26" }),
      ),
    );
  });

  it("preserves the season when opening a player", async () => {
    renderPlayers("/players?season=2025-26");

    await userEvent.click(await screen.findByRole("button", { name: /Stephen Curry/i }));

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/players/1?season=2025-26",
    );
    await waitFor(() => expect(getPlayer).toHaveBeenCalledWith(1, "2025-26"));
    expect(await screen.findByText(/2025-26 season/i)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /back to players/i }));
    expect(screen.getByTestId("location")).toHaveTextContent(
      "/players?season=2025-26",
    );
  });

  it("does not request unscoped players when no seasons are imported", async () => {
    vi.mocked(getPlayerSeasons).mockResolvedValue([]);

    renderPlayers();

    expect(
      await screen.findByText(/no player seasons imported/i),
    ).toBeInTheDocument();
    expect(getPlayers).not.toHaveBeenCalled();
  });
});
