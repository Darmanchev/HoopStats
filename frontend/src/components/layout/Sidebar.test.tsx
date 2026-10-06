import {render,screen} from "@testing-library/react";
import {MemoryRouter} from "react-router-dom";
import {expect,it} from "vitest";
import Sidebar from "./Sidebar";
it("labels navigation and marks only the matching route active",()=>{
 render(<MemoryRouter initialEntries={["/players"]}><Sidebar/></MemoryRouter>);
 expect(screen.getByRole("navigation",{name:"Main navigation"})).toBeInTheDocument();
 expect(screen.getByRole("link",{name:"Players"})).toHaveAttribute("aria-current","page");
 expect(screen.getByRole("link",{name:"Dashboard"})).not.toHaveAttribute("aria-current");
});
