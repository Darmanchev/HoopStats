import { useState, useEffect } from "react";
import type { Player } from "../types";
import { getPlayers } from "../lib/api";

interface UsePlayersOptions {
  sortBy?: string;
  team?: string;
  position?: string;
  minGames?: number;
  limit?: number;
}

export function usePlayers(options?: UsePlayersOptions) {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPlayers({
      sort_by: options?.sortBy || "pts",
      team: options?.team,
      position: options?.position,
      min_games: options?.minGames ?? 10,
      limit: options?.limit ?? 200,
    })
      .then(setPlayers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [options?.sortBy, options?.team, options?.position, options?.minGames, options?.limit]);

  return { players, loading, error };
}
