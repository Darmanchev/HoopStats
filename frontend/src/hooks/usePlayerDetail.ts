import { useState, useEffect } from "react";
import type { PlayerDetail } from "../types";
import { getPlayer } from "../lib/api";

/** Загружает детальную карточку игрока по id. */
export function usePlayerDetail(id: string | undefined) {
  const [player, setPlayer] = useState<PlayerDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    getPlayer(parseInt(id))
      .then((p) => !cancelled && setPlayer(p))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [id]);

  return { player, loading, error };
}
