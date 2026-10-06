import { useCallback, useEffect, useState } from "react";
import type { LiveGame } from "../types";
import { getMatch, getTeamStats, getTeams, getBoxScore, getSyncStatus } from "../lib/api";
import { useRemote } from "./useRemote";

export function useMatch(id: string | undefined) {
  const [tick, setTick] = useState(0);
  const loadGame = useCallback(() => getMatch(id!), [id]);
  const match = useRemote(id ?? null, loadGame, tick);
  const game: LiveGame | null = match.data ?? null;
  const awayAbbr = game?.team1;
  const homeAbbr = game?.team2;
  const season = game?.season;

  const loadTeams = useCallback(() => getTeams(), []);
  const teams = useRemote("teams", loadTeams);
  const loadAway = useCallback(() => getTeamStats(awayAbbr!, season), [awayAbbr, season]);
  const loadHome = useCallback(() => getTeamStats(homeAbbr!, season), [homeAbbr, season]);
  const away = useRemote(game ? `${id}:${awayAbbr}:${season}` : null, loadAway, tick);
  const home = useRemote(game ? `${id}:${homeAbbr}:${season}` : null, loadHome, tick);
  const loadBox = useCallback(() => getBoxScore(id!), [id]);
  const box = useRemote(game && game.status !== "scheduled" ? `${id}:box` : null, loadBox, tick);
  const loadSource = useCallback(() => getSyncStatus(), []);
  const source = useRemote("source", loadSource, tick);

  useEffect(() => {
    if (game?.status !== "live") return;
    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") setTick(value => value + 1);
    }, 30_000);
    return () => window.clearInterval(interval);
  }, [game?.status]);

  return {
    game,
    teams: teams.data ?? {},
    stats: game ? {[game.team1]: away.data, [game.team2]: home.data} : {},
    loading: match.loading,
    error: match.error,
    teamError: teams.error,
    statsErrors: game ? {[game.team1]: away.error, [game.team2]: home.error} : {},
    boxScore: box.data ?? [],
    boxLoading: box.loading,
    boxError: box.error,
    sourceStatus: source.data ?? {},
    retry: match.retry,
    retryTeams: teams.retry,
    retryStats: game ? {[game.team1]: away.retry, [game.team2]: home.retry} : {},
    retryBox: box.retry,
  };
}
