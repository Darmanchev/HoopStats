import { useState, useEffect } from "react";
import type { Team, TeamStats } from "../types";
import { getTeams, getTeamStats } from "../lib/api";

/** Загружает команду по abbr + её статистику (форма, последние очки). */
export function useTeamDetail(abbr: string | undefined) {
  const [team, setTeam] = useState<Team | null>(null);
  const [stats, setStats] = useState<TeamStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [completedRequest, setCompletedRequest] = useState<string | null>(null);

  useEffect(() => {
    if (!abbr) return;
    let cancelled = false;

    Promise.all([getTeams(), getTeamStats(abbr)])
      .then(([teamsMap, teamStats]) => {
        if (cancelled) return;
        const found = teamsMap[abbr];
        if (!found) {
          setError("Team not found");
          return;
        }
        setTeam(found);
        setStats(teamStats);
        setError(null);
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setCompletedRequest(abbr));

    return () => {
      cancelled = true;
    };
  }, [abbr]);

  return {
    team,
    stats,
    loading: Boolean(abbr) && completedRequest !== abbr,
    error,
  };
}
