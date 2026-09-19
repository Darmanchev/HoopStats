import { useState, useEffect } from "react";
import type { UpcomingGame, PastGame } from "../types";
import { getUpcomingGames, getPastGames } from "../lib/api";

/**
 * Загружает игры. С аргументом `season` отдаёт прошедшие игры только
 * выбранного сезона, а предстоящие фильтрует под него же (предстоящие
 * существуют лишь у текущего сезона). Без аргумента — всё.
 */
export function useGames(season?: string, includePast = true) {
  const [upcoming, setUpcoming] = useState<UpcomingGame[]>([]);
  const [past, setPast] = useState<PastGame[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [completedRequest, setCompletedRequest] = useState<string | null>(null);
  const requestKey = `${season ?? "all"}:${includePast}`;

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      getUpcomingGames(),
      includePast ? getPastGames(season) : Promise.resolve([]),
    ])
      .then(([upcomingData, pastData]) => {
        if (cancelled) return;
        setUpcoming(
          season ? upcomingData.filter((g) => g.season === season) : upcomingData
        );
        setPast(pastData);
        setError(null);
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setCompletedRequest(requestKey));

    return () => {
      cancelled = true;
    };
  }, [season, includePast, requestKey]);

  return {
    upcoming,
    past,
    loading: completedRequest !== requestKey,
    error,
  };
}
