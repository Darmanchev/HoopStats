import { useState, useEffect } from "react";
import type { UpcomingGame, PastGame } from "../types";
import { getUpcomingGames, getPastGames } from "../lib/api";

export function useGames() {
  const [upcoming, setUpcoming] = useState<UpcomingGame[]>([]);
  const [past, setPast] = useState<PastGame[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getUpcomingGames(), getPastGames()])
      .then(([upcomingData, pastData]) => {
        setUpcoming(upcomingData);
        setPast(pastData);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { upcoming, past, loading, error };
}
