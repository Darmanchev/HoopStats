import { useState, useEffect } from "react";
import type { UpcomingGame, Team, TeamStats } from "../types";
import { getMatch, getTeamStats, getTeams } from "../lib/api";

/**
 * Загружает матч + словарь команд + статистику обеих команд.
 * `cancelled` защищает от setState после размонтирования / смены id.
 */
export function useMatch(id: string | undefined) {
  const [game, setGame] = useState<UpcomingGame | null>(null);
  const [teams, setTeams] = useState<Record<string, Team>>({});
  const [stats, setStats] = useState<Record<string, TeamStats>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([getMatch(id), getTeams()])
      .then(([gameData, teamsData]) => {
        if (cancelled) return;
        setGame(gameData);
        setTeams(teamsData);
        // Берём team1/team2 из gameData (state ещё не обновлён в этом замыкании)
        return Promise.all([
          getTeamStats(gameData.team1),
          getTeamStats(gameData.team2),
        ]).then(([s1, s2]) => {
          if (cancelled) return;
          setStats({ [gameData.team1]: s1, [gameData.team2]: s2 });
        });
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [id]);

  return { game, teams, stats, loading, error };
}
