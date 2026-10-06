import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, it, vi } from "vitest";
import PlayerGameLog from "./PlayerGameLog";
import { getPlayerGames } from "../../lib/api";
vi.mock("../../lib/api",()=>({getPlayerGames:vi.fn()}));
it("explains incomplete imported coverage rather than inventing a log",async()=>{
 vi.mocked(getPlayerGames).mockResolvedValue({items:[],total:0,coverage:{identityResolved:true,importedGames:0,note:"Only imported box scores are available."}});
 render(<MemoryRouter><PlayerGameLog id={1} season="2024-25"/></MemoryRouter>);
 await screen.findByText("No game logs imported for this player and season");
 expect(screen.getByText("Only imported box scores are available.")).toBeInTheDocument();
 expect(getPlayerGames).toHaveBeenCalledWith(1,"2024-25",0);
});
