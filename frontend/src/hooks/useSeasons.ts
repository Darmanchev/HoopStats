import { useState, useEffect } from "react";
import { getSeasons } from "../lib/api";

/** Список доступных сезонов (отсортирован от свежего к старому). */
export function useSeasons() {
  const [seasons, setSeasons] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    getSeasons()
      .then((s) => !cancelled && setSeasons(s))
      .catch(() => {
        /* выпадашка просто останется пустой */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return seasons;
}
