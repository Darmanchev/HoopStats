import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { it, expect, vi } from "vitest";
import Schedule from "./Schedule";

vi.mock("../hooks/useSeasons", () => ({ useSeasons: () => ["2026-27"] }));
vi.mock("../hooks/useTeams", () => ({ useTeams: () => ({
  loading: false, error: null, teams: {
    MIA: { abbr: "MIA", name: "Heat", city: "Miami", record: "0-0" },
    TOR: { abbr: "TOR", name: "Raptors", city: "Toronto", record: "0-0" },
  },
}) }));
vi.mock("../hooks/useGames", () => ({ useGames: () => ({
  loading: false, error: null, upcoming: [], past: [
    { id: "0012600009", team1: "MIA", team2: "TOR", date: "2026-10-03",
      season: "2026-27", seasonType: "preseason", score1: 129, score2: 105 },
    { id: "0022600001", team1: "MIA", team2: "TOR", date: "2026-10-22",
      season: "2026-27", seasonType: "regular", score1: 110, score2: 100 },
  ],
}) }));

it("separates preseason games from regular-season results", async () => {
  const user = userEvent.setup();
  render(<MemoryRouter><Schedule /></MemoryRouter>);
  expect(screen.getByText("129")).toBeInTheDocument();
  expect(screen.getByText("110")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Preseason" }));
  expect(screen.getByText("129")).toBeInTheDocument();
  expect(screen.queryByText("110")).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Regular Season" }));
  expect(screen.queryByText("129")).not.toBeInTheDocument();
  expect(screen.getByText("110")).toBeInTheDocument();
});
