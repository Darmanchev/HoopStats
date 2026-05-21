import { useState, useEffect } from "react";
import type { Player } from "../types";
import { getElo, getLeaders, type EloEntry } from "../lib/api";

/** Загружает данные страницы Analytics: Elo-рейтинги и лидеров лиги. */
export function useAnalytics() {
  const [elo, setElo] = useState<EloEntry[]>([]);
  const [leaders, setLeaders] = useState<Record<string, Player[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    Promise.all([getElo(), getLeaders()])
      .then(([eloData, leadersData]) => {
        if (cancelled) return;
        setElo(eloData);
        setLeaders(leadersData);
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, []);

  return { elo, leaders, loading, error };
}
