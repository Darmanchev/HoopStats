import { useEffect, useState } from "react";

import { getPlayerSeasons } from "../lib/api";


export function usePlayerSeasons() {
  const [seasons, setSeasons] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    getPlayerSeasons()
      .then((result) => {
        if (!cancelled) setSeasons(result);
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Unable to load seasons");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { seasons, loading, error };
}
