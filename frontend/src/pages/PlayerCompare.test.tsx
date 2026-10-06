import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, it, vi } from "vitest";
import PlayerCompare from "./PlayerCompare";
import * as api from "../lib/api";
vi.mock("../hooks/usePlayerSeasons",()=>({usePlayerSeasons:()=>({seasons:["2024-25"],loading:false,error:null})}));
vi.mock("../lib/api",()=>({getPlayer:vi.fn(),getPlayers:vi.fn()}));
it("uses one selected season for both players",async()=>{
 vi.mocked(api.getPlayers).mockResolvedValue([]);
 vi.mocked(api.getPlayer).mockRejectedValue(new Error("Player season not found"));
 render(<MemoryRouter initialEntries={["/players/compare?left=1&right=2&season=2024-25"]}><PlayerCompare/></MemoryRouter>);
 await screen.findAllByText("Player season not found");
 expect(api.getPlayer).toHaveBeenCalledWith(1,"2024-25");
 expect(api.getPlayer).toHaveBeenCalledWith(2,"2024-25");
});
