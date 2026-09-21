import { useState, useEffect } from "react";
import type { Team, TeamStats } from "../types";
import { getTeams } from "../lib/api";

export function useAllTeams() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [stats, setStats] = useState<Record<string, TeamStats>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTeams()
      .then((teamsMap) => {
        const list = Object.values(teamsMap);
        setTeams(list);

        const statsMap: Record<string, TeamStats> = {};
        list.forEach((team) => {
          if (team.stats) statsMap[team.abbr] = team.stats;
        });
        setStats(statsMap);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { teams, stats, loading, error };
}
