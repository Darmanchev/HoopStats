import { useEffect, useState } from "react";
import { getTeamSeasons } from "../lib/api";

export function useTeamSeasons() {
  const [result, setResult] = useState<{
    seasons: string[]; error: string | null; loading: boolean;
  }>({ seasons: [], error: null, loading: true });
  useEffect(() => {
    let cancelled = false;
    getTeamSeasons()
      .then((seasons) => {
        if (!cancelled) setResult({ seasons, error: null, loading: false });
      })
      .catch((error) => {
        if (!cancelled) setResult({ seasons: [], error: error.message, loading: false });
      });
    return () => { cancelled = true; };
  }, []);
  return result;
}
