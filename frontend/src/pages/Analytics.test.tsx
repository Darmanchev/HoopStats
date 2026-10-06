import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, it, vi } from "vitest";
import Analytics from "./Analytics";
vi.mock("../lib/api",()=>({getElo:vi.fn().mockResolvedValue([]),getLeaders:vi.fn().mockResolvedValue({}),getDashboardSeason:vi.fn().mockResolvedValue({season:"2024-25",seasons:["2024-25"],teams:[],leaders:{},teamsAvailable:false,playersAvailable:false}),getModelPerformance:vi.fn().mockResolvedValue({available:false,reason:"Model evaluation unavailable",games:[],total:0})}));
vi.mock("../hooks/useTeams",()=>({useTeams:()=>({teams:{},loading:false,error:null})}));
it("uses imported season labels and shows missing datasets and evaluation",async()=>{
 render(<MemoryRouter><Analytics/></MemoryRouter>);
 await screen.findByText(/League insights · 2024–25 season/);
 expect(screen.getByText(/No completed games/)).toBeInTheDocument();
 expect(screen.getByText(/No player leaders/)).toBeInTheDocument();
 await screen.findByText("Model evaluation unavailable");
});
