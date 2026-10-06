import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import MatchDetail from "./MatchDetail";
import * as api from "../lib/api";
vi.mock("../lib/api", () => ({ getMatch:vi.fn(),getTeams:vi.fn(),getTeamStats:vi.fn(),getBoxScore:vi.fn(),getSyncStatus:vi.fn() }));
const teams = { BOS:{abbr:"BOS",city:"Boston",name:"Celtics",record:"0-0"}, LAL:{abbr:"LAL",city:"LA",name:"Lakers",record:"0-0"} };
beforeEach(() => {
  vi.mocked(api.getMatch).mockResolvedValue({id:"g",team1:"BOS",team2:"LAL",date:"2026-10-01",time:"",venue:"",season:"2026-27",seasonType:"regular",isToday:false,win1:null,prediction:null,status:"final",statusText:"Final",score1:100,score2:90,period:null,clock:null});
  vi.mocked(api.getTeams).mockResolvedValue(teams);
  vi.mocked(api.getTeamStats).mockRejectedValue(new Error("Stats unavailable"));
  vi.mocked(api.getBoxScore).mockResolvedValue([]);
  vi.mocked(api.getSyncStatus).mockResolvedValue({});
});
it("preserves the match when statistics fail and does not invent probabilities", async () => {
 render(<MemoryRouter initialEntries={["/match/g"]}><Routes><Route path="/match/:id" element={<MatchDetail/>}/></Routes></MemoryRouter>);
 await waitFor(() => expect(screen.getByText("100")).toBeInTheDocument());
 expect(screen.getByText("Prediction unavailable")).toBeInTheDocument();
 expect(screen.queryByText(/50%/)).not.toBeInTheDocument();
 expect(await screen.findAllByText("Stats unavailable")).toHaveLength(2);
});

it("refreshes a visible live match every 30 seconds and stops polling on unmount", async () => {
  const game = await api.getMatch("g");
  vi.mocked(api.getMatch).mockResolvedValue({...game,status:"live",statusText:"",period:2,clock:"04:12"});
  const callback = {current:()=>{}};
  const interval = vi.spyOn(window,"setInterval").mockImplementation((handler,timeout)=>{if(timeout===30000) callback.current=handler as ()=>void;return 123;});
  const clear = vi.spyOn(window,"clearInterval");
  const view = render(<MemoryRouter initialEntries={["/match/g"]}><Routes><Route path="/match/:id" element={<MatchDetail/>}/></Routes></MemoryRouter>);
  await screen.findByText(/Period 2/);
  const previous = vi.mocked(api.getMatch).mock.calls.length;
  const {act} = await import("@testing-library/react");
  await act(async()=>callback.current());
  await waitFor(()=>expect(api.getMatch).toHaveBeenCalledTimes(previous+1));
  view.unmount();
  expect(clear).toHaveBeenCalledWith(123);
  interval.mockRestore();clear.mockRestore();
});
