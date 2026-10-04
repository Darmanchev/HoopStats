import { describe, expect, it } from "vitest";
import { formatGameTime } from "./gameTime";

describe("game time", () => {
  it("formats ISO timestamps as a compact local time", () => {
    const timestamp = "2026-10-20T19:00:00Z";
    const expected = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", timeZoneName: "short" }).format(new Date(timestamp));
    expect(formatGameTime({ time: timestamp })).toBe(expected);
    expect(formatGameTime({ time: "Scheduled", startTime: timestamp })).toBe(expected);
  });
  it("preserves legacy time labels and handles missing or invalid timestamps", () => {
    expect(formatGameTime({ time: "7:30 PM ET" })).toBe("7:30 PM ET");
    expect(formatGameTime({ time: "" })).toBe("Time TBA");
    expect(formatGameTime({ time: "2026-10-20Tinvalid" })).toBe("Time TBA");
  });
});
