import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router-dom";
import { expect, it, vi } from "vitest";
import GlobalSearch from "./GlobalSearch";
import { getSearch } from "../../lib/api";
vi.mock("../../lib/api", () => ({getSearch:vi.fn()}));
function Location(){ return <p>{useLocation().pathname}</p>; }
it("searches after typing and supports Enter and Escape", async () => {
 vi.mocked(getSearch).mockResolvedValue({players:[{id:"1",label:"Curry",url:"/players/1"}],teams:[],games:[]});
 const user = userEvent.setup();
 render(<MemoryRouter><GlobalSearch/><Location/></MemoryRouter>);
 await user.type(screen.getByRole("combobox"),"Cu");
 await screen.findByRole("option",{name:/Curry/});
 await user.keyboard("{ArrowDown}{Enter}");
 expect(screen.getByText("/players/1")).toBeInTheDocument();
 await user.type(screen.getByRole("combobox"),"Cu");
 await screen.findByRole("option",{name:/Curry/});
 await user.keyboard("{Escape}");
 expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
});
