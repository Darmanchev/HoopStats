import { useCallback, useState } from "react";
import { getDashboardSeason, getElo, getLeaders } from "../lib/api";
import { useRemote } from "./useRemote";

export function useAnalytics() {
  const [selectedSeason,setSelectedSeason] = useState<string>();
  const loadSeason = useCallback(()=>getDashboardSeason(selectedSeason),[selectedSeason]);
  const seasons = useRemote(`analytics:${selectedSeason ?? "latest"}`,loadSeason);
  const season = seasons.data?.season ?? undefined;
  const loadElo = useCallback(()=>getElo(season),[season]);
  const loadLeaders = useCallback(()=>getLeaders(season),[season]);
  const elo = useRemote(season ? `elo:${season}` : null,loadElo);
  const leaders = useRemote(season ? `leaders:${season}` : null,loadLeaders);
  return {season,selectedSeason,setSelectedSeason,seasons:seasons.data?.seasons ?? [],elo:elo.data ?? [],leaders:leaders.data ?? {},
    loading:seasons.loading || elo.loading || leaders.loading,error:seasons.error,eloError:elo.error,leadersError:leaders.error,
    retry:seasons.retry,retryElo:elo.retry,retryLeaders:leaders.retry};
}
