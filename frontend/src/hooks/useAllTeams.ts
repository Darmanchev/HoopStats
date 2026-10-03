import { useState, useEffect } from "react";
import type { Team, TeamStats } from "../types";
import { getTeams } from "../lib/api";

export function useAllTeams(season?: string, enabled = true) {
  const key = enabled ? season ?? "current" : null;
  const [result, setResult] = useState<{
    key: string; teams: Team[]; error: string | null;
  } | null>(null);

  useEffect(() => {
    if (key === null) return;
    let cancelled = false;
    getTeams(season)
      .then((teamsMap) => {
        if (!cancelled) setResult({ key, teams: Object.values(teamsMap), error: null });
      })
      .catch((e) => {
        if (!cancelled) setResult({ key, teams: [], error: e.message });
      });
    return () => { cancelled = true; };
  }, [key, season]);

  const current = key !== null && result?.key === key;
  const teams = current ? result.teams : [];
  const stats: Record<string, TeamStats> = {};
  teams.forEach((team) => { if (team.stats) stats[team.abbr] = team.stats; });
  return { teams, stats, loading: key !== null && !current, error: current ? result.error : null };
}
