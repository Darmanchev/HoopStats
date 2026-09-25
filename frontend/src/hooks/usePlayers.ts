import { useEffect, useState } from "react";

import { getPlayers } from "../lib/api";
import type { Player } from "../types";

interface UsePlayersOptions {
  sortBy?: string;
  team?: string;
  position?: string;
  minGames?: number;
  limit?: number;
  season?: string;
  enabled?: boolean;
}


interface PlayersResult {
  key: string;
  players: Player[];
  error: string | null;
}


function messageFrom(caught: unknown): string {
  if (
    typeof caught === "object"
    && caught !== null
    && "message" in caught
    && typeof caught.message === "string"
  ) {
    return caught.message;
  }
  return "Unable to load players";
}


export function usePlayers(options?: UsePlayersOptions) {
  const enabled = options?.enabled !== false;
  const requestKey = enabled
    ? JSON.stringify([
        options?.sortBy ?? "pts",
        options?.team ?? "",
        options?.position ?? "",
        options?.minGames ?? 10,
        options?.limit ?? 200,
        options?.season ?? "",
      ])
    : null;
  const [result, setResult] = useState<PlayersResult | null>(null);

  useEffect(() => {
    if (requestKey === null) return;
    let cancelled = false;

    getPlayers({
      sort_by: options?.sortBy || "pts",
      team: options?.team,
      position: options?.position,
      min_games: options?.minGames ?? 10,
      limit: options?.limit ?? 200,
      season: options?.season,
    })
      .then((players) => {
        if (!cancelled) {
          setResult({ key: requestKey, players, error: null });
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setResult({
            key: requestKey,
            players: [],
            error: messageFrom(caught),
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [
    requestKey,
    options?.sortBy,
    options?.team,
    options?.position,
    options?.minGames,
    options?.limit,
    options?.season,
  ]);

  const current = requestKey !== null && result?.key === requestKey;
  return {
    players: current ? result.players : [],
    loading: requestKey !== null && !current,
    error: current ? result.error : null,
  };
}
