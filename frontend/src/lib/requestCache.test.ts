import { describe, expect, it, vi } from "vitest";

import { cachedRequest } from "./requestCache";


describe("cachedRequest", () => {
  it("reuses one in-flight request for the same key", async () => {
    const loader = vi.fn().mockResolvedValue(["BOS"]);

    const first = cachedRequest("teams-inflight", 30_000, loader);
    const second = cachedRequest("teams-inflight", 30_000, loader);

    expect(first).toBe(second);
    await first;
    expect(loader).toHaveBeenCalledTimes(1);
  });

  it("removes a rejected request so the next call retries", async () => {
    const loader = vi
      .fn()
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(["BOS"]);

    await expect(cachedRequest("teams-retry", 30_000, loader)).rejects.toThrow(
      "offline",
    );
    await expect(
      cachedRequest("teams-retry", 30_000, loader),
    ).resolves.toEqual(["BOS"]);
    expect(loader).toHaveBeenCalledTimes(2);
  });
});
