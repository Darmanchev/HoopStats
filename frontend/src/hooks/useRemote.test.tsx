import { act, renderHook, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { useRemote } from "./useRemote";
it("discards a late result after the resource key changes",async()=>{
 let finish!: (data:string)=>void;
 const old = () => new Promise<string>(resolve=>{finish=resolve;});
 const next = () => Promise.resolve("new");
 const hook = renderHook(({key,loader})=>useRemote(key,loader),{initialProps:{key:"old",loader:old}});
 await waitFor(()=>expect(finish).toBeDefined());
 hook.rerender({key:"new",loader:next});
 await waitFor(()=>expect(hook.result.current.data).toBe("new"));
 await act(async()=>finish("old"));
 expect(hook.result.current.data).toBe("new");
});
it("keeps successful data visible when a background refresh fails",async()=>{
 const loader = vi.fn().mockResolvedValueOnce("score").mockRejectedValueOnce(new Error("Offline"));
 const hook = renderHook(({tick})=>useRemote("game",loader,tick),{initialProps:{tick:0}});
 await waitFor(()=>expect(hook.result.current.data).toBe("score"));
 hook.rerender({tick:1});
 expect(hook.result.current.loading).toBe(false);
 await waitFor(()=>expect(hook.result.current.error).toBe("Offline"));
 expect(hook.result.current.data).toBe("score");
});
