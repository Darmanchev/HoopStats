import { useState, useEffect } from "react";
import type { Injury } from "../types";
import { getInjuries } from "../lib/api";

export function useInjuries() {
  const [injuries, setInjuries] = useState<Injury[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getInjuries()
      .then(setInjuries)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { injuries, loading, error };
}
