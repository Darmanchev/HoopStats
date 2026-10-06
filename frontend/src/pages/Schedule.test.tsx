import { useGameSeasons } from "../hooks/useSeasons";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { it, expect, vi } from "vitest";
import Schedule from "./Schedule";
import * as api from "../lib/api";
vi.mock("../lib/api", () => ({getSchedule:vi.fn(),getScheduleMonths:vi.fn()}));
vi.mock("../hooks/useSeasons", () => ({useGameSeasons:vi.fn(()=>({seasons:["2026-27"],loading:false,error:undefined,retry:vi.fn()}))}));
vi.mock("../hooks/useTeams", () => ({useTeams:() => ({loading:false,error:null,teams:{MIA:{abbr:"MIA",name:"Heat",city:"Miami",record:"0-0"},TOR:{abbr:"TOR",name:"Raptors",city:"Toronto",record:"0-0"}}})}));
it("sends competition and paging filters to the server", async () => {
 vi.mocked(api.getScheduleMonths).mockResolvedValue(["2026-10"]);
 vi.mocked(api.getSchedule).mockImplementation(async params => ({total:101,items:[{id:"g",team1:"MIA",team2:"TOR",date:"2026-10-03",season:"2026-27",seasonType:params.season_type === "preseason" ? "preseason" : "regular",score1:129,score2:105,status:"final",statusText:"Final",period:null,clock:null,win1:null,prediction:null,isToday:false,time:"",venue:""}]}));
 const user = userEvent.setup();
 render(<MemoryRouter><Schedule/></MemoryRouter>);
 await screen.findByText("129");
 await user.click(screen.getByRole("button",{name:"Preseason"}));
 await waitFor(() => expect(api.getSchedule).toHaveBeenLastCalledWith(expect.objectContaining({season_type:"preseason",skip:0,limit:50})));
 await screen.findByText("129");
 await user.click(screen.getByRole("button",{name:"Next"}));
 await waitFor(() => expect(api.getSchedule).toHaveBeenLastCalledWith(expect.objectContaining({skip:50})));
});

it("shows an empty state when no game seasons have been imported",async()=>{
 vi.mocked(useGameSeasons).mockReturnValueOnce({seasons:[],loading:false,error:undefined,retry:vi.fn()});
 render(<MemoryRouter><Schedule/></MemoryRouter>);
 expect(screen.getByText("No game seasons imported")).toBeInTheDocument();
});

it("resets the page when the active favorite-team subset changes in another tab",async()=>{
 localStorage.setItem("hoopstats:favorites:v1",JSON.stringify({version:1,teams:["MIA","TOR"],players:[]}));
 vi.mocked(api.getSchedule).mockResolvedValue({total:200,items:[]});
 vi.mocked(api.getScheduleMonths).mockResolvedValue([]);
 const user = userEvent.setup();
 render(<MemoryRouter><Schedule/></MemoryRouter>);
 await waitFor(()=>expect(api.getSchedule).toHaveBeenCalled());
 await user.click(screen.getByRole("button",{name:"Favorite teams"}));
 await waitFor(()=>expect(api.getSchedule).toHaveBeenLastCalledWith(expect.objectContaining({team:"MIA,TOR",skip:0})));
 await user.click(screen.getByRole("button",{name:"Next"}));
 await waitFor(()=>expect(api.getSchedule).toHaveBeenLastCalledWith(expect.objectContaining({skip:50})));
 localStorage.setItem("hoopstats:favorites:v1",JSON.stringify({version:1,teams:["TOR"],players:[]}));
 const {act} = await import("@testing-library/react");
 await act(async()=>window.dispatchEvent(new StorageEvent("storage",{key:"hoopstats:favorites:v1"})));
 await waitFor(()=>expect(api.getSchedule).toHaveBeenLastCalledWith(expect.objectContaining({team:"TOR",skip:0})));
});
