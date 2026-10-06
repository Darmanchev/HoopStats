import type { UpcomingGame } from "../types";

/** Format scheduled timestamps in the viewer's timezone; keep legacy time labels. */
export function formatGameTime(game: Pick<UpcomingGame, "time" | "startTime">, showTimezone = true): string {
  const timestamp = game.startTime || (/^\d{4}-\d{2}-\d{2}T/.test(game.time) ? game.time : null);
  if (timestamp) {
    const date = new Date(timestamp);
    if (!Number.isNaN(date.getTime())) {
      return new Intl.DateTimeFormat("en-US", {
        hour: "numeric", minute: "2-digit",
        ...(showTimezone ? { timeZoneName: "short" as const } : {}),
      }).format(date);
    }
  }
  return /^\d{4}-\d{2}-\d{2}T/.test(game.time) ? "Time TBA" : game.time || "Time TBA";
}
