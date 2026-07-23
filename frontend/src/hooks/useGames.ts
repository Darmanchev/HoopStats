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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

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
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [season, includePast]);

  return { upcoming, past, loading, error };
}
