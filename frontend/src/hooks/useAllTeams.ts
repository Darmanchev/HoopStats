import { useState, useEffect } from "react";
import type { Team, TeamStats } from "../types";
import { getTeams, getTeamStats } from "../lib/api";

export function useAllTeams() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [stats, setStats] = useState<Record<string, TeamStats>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTeams()
      .then(async (teamsMap) => {
        const list = Object.values(teamsMap);
        setTeams(list);

        const statsPromises = list.map((t) =>
          getTeamStats(t.abbr).catch(() => null)
        );
        const results = await Promise.all(statsPromises);
        const statsMap: Record<string, TeamStats> = {};
        list.forEach((t, i) => {
          if (results[i]) statsMap[t.abbr] = results[i];
        });
        setStats(statsMap);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { teams, stats, loading, error };
}
