import { act, renderHook } from "@testing-library/react";
import { expect, it } from "vitest";
import { useFavorites } from "./useFavorites";
it("ignores invalid storage and notifies same-tab subscribers", () => {
 localStorage.setItem("hoopstats:favorites:v1", "broken");
 const first = renderHook(useFavorites); const second = renderHook(useFavorites);
 expect(first.result.current.teams).toEqual([]);
 act(() => first.result.current.toggleTeam("BOS"));
 expect(second.result.current.teams).toEqual(["BOS"]);
 act(() => first.result.current.togglePlayer(7));
 expect(second.result.current.players).toEqual([7]);
 expect(JSON.parse(localStorage.getItem("hoopstats:favorites:v1")!).teams).toEqual(["BOS"]);
 act(() => first.result.current.toggleTeam("BOS"));
 expect(second.result.current.teams).toEqual([]);
});
