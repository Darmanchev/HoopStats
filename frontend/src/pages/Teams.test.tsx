import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getTeams, getTeamSeasons } from "../lib/api";
import Teams from "./Teams";
import type { Team } from "../types";

vi.mock("../lib/api", () => ({ getTeams: vi.fn(), getTeamSeasons: vi.fn() }));

const team: Team = { abbr: "BOS", city: "Boston", name: "Celtics", record: "2-1" };
function Location() {
  const location = useLocation();
  return <output data-testid="location">{location.pathname}{location.search}</output>;
}
function show(entry = "/teams") {
  render(<MemoryRouter initialEntries={[entry]}><Routes>
    <Route path="/teams" element={<Teams />} />
    <Route path="/teams/:abbr" element={<div>Team details</div>} />
  </Routes><Location /></MemoryRouter>);
}

describe("Teams seasons", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getTeamSeasons).mockResolvedValue(["2024-25", "2023-24"]);
    vi.mocked(getTeams).mockImplementation(async (season) => ({ BOS: { ...team, record: season === "2023-24" ? "0-1" : "2-1" } }));
  });
  it("defaults to the latest season and loads different records when switching", async () => {
    show();
    const selector = await screen.findByRole("combobox", { name: "Season" });
    await waitFor(() => expect(getTeams).toHaveBeenLastCalledWith("2024-25"));
    expect(await screen.findByText(/^2-1 ·/)).toBeInTheDocument();
    await userEvent.selectOptions(selector, "2023-24");
    await waitFor(() => expect(getTeams).toHaveBeenLastCalledWith("2023-24"));
    expect(await screen.findByText(/^0-1 ·/)).toBeInTheDocument();
    expect(screen.getByTestId("location")).toHaveTextContent("/teams?season=2023-24");
  });
  it("preserves an explicit season when opening a team", async () => {
    show("/teams?season=2023-24");
    const card = await screen.findByRole("button", { name: /^Open team.*Celtics/i });
    await userEvent.click(card);
    expect(screen.getByTestId("location")).toHaveTextContent("/teams/BOS?season=2023-24");
  });
  it("shows a disabled selector when no games are imported", async () => {
    vi.mocked(getTeamSeasons).mockResolvedValue([]);
    show();
    expect(await screen.findByRole("combobox", { name: "Season" })).toBeDisabled();
    expect(await screen.findByText(/Season records will be available/)).toBeInTheDocument();
  });
  it("does not let a stale response replace the selected season", async () => {
    let finishOld!: (teams: Record<string, Team>) => void;
    vi.mocked(getTeams).mockImplementation((season) => season === "2024-25"
      ? new Promise((resolve) => { finishOld = resolve; })
      : Promise.resolve({ BOS: { ...team, record: "0-1" } }));
    show();
    const selector = await screen.findByRole("combobox", { name: "Season" });
    await waitFor(() => expect(getTeams).toHaveBeenCalledWith("2024-25"));
    await userEvent.selectOptions(selector, "2023-24");
    expect(await screen.findByText(/^0-1 ·/)).toBeInTheDocument();
    finishOld({ BOS: team });
    await waitFor(() => expect(screen.queryByText(/^2-1 ·/)).not.toBeInTheDocument());
  });
});
