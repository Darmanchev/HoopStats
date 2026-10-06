import { useCallback } from "react";
import { getSeasons } from "../lib/api";
import { useRemote } from "./useRemote";

export function useGameSeasons() {
  const loader = useCallback(() => getSeasons(), []);
  const result = useRemote("game-seasons", loader);
  return {seasons:result.data ?? [],loading:result.loading,error:result.error,retry:result.retry};
}
export function useSeasons() { return useGameSeasons().seasons; }
