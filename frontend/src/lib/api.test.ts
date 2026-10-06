import { afterEach, expect, it, vi } from "vitest";
import { getModelPerformance, retrySync } from "./api";
afterEach(()=>vi.unstubAllGlobals());
it("sends retry source and token only in the POST body and access header",async()=>{
 const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>({queued:true})});
 vi.stubGlobal("fetch",fetch);
 expect(await retrySync("sync_players","secret")).toEqual({queued:true});
 expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/\/analytics\/sync-retry$/),{method:"POST",headers:{"Content-Type":"application/json","X-Sync-Token":"secret"},body:'{"source":"sync_players"}'});
});
it("does not expose response content or tokens in retry failures",async()=>{
 vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:false,status:403,statusText:"secret"}));
 await expect(retrySync("sync_players","secret")).rejects.toEqual({status:403,message:"Retry failed (403)",name:"ApiError"});
});
it("encodes the evaluation season with pagination",async()=>{
 const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>({games:[]})});vi.stubGlobal("fetch",fetch);
 await getModelPerformance(20,"2023-24");
 expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/model-performance\?skip=20&limit=20&season=2023-24$/));
});
