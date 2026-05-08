import { useEffect, useState } from "react";
import { getTeams } from "../lib/api";
import type { Team } from "../types";

export function useTeams() {
  const [teams, setTeams] = useState<Record<string, Team>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTeams()
      .then(setTeams)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { teams, loading, error };
}
