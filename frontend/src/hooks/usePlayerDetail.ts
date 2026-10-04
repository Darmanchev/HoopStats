import { useState, useEffect } from "react";
import type { PlayerDetail } from "../types";
import { getPlayer } from "../lib/api";

/** Загружает детальную карточку игрока по id. */
export function usePlayerDetail(id: string | undefined, season?: string) {
  const [player, setPlayer] = useState<PlayerDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [completedRequest, setCompletedRequest] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    const requestKey = `${id}:${season ?? ""}`;

    getPlayer(parseInt(id, 10), season)
      .then((p) => {
        if (cancelled) return;
        setPlayer(p);
        setError(null);
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setCompletedRequest(requestKey));

    return () => {
      cancelled = true;
    };
  }, [id, season]);

  const requestKey = id ? `${id}:${season ?? ""}` : null;

  return {
    player,
    loading: Boolean(id) && completedRequest !== requestKey,
    error,
  };
}
