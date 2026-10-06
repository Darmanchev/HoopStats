import { useCallback } from "react";
import { Link } from "react-router-dom";
import { getPlayers } from "../../lib/api";
import { useRemote } from "../../hooks/useRemote";
import { useFavorites } from "../../hooks/useFavorites";
import type { Team } from "../../types";
export default function FavoritesWidget({teams}:{teams:Record<string,Team>}) {
  const favorites = useFavorites();
  const ids = favorites.players.join(",");
  const loader = useCallback(()=>getPlayers({ids,limit:200,min_games:0}),[ids]);
  const players = useRemote(ids || null,loader);
  return <section className="bg-surface border border-line rounded-2xl p-5 mb-6">
    <h2 className="font-bold text-lg mb-3">Your favorites</h2>
    {!favorites.teams.length && !favorites.players.length ? <p className="text-muted text-sm">Save teams and players from their cards or profiles.</p> : <div className="flex flex-wrap gap-3">
      {favorites.teams.map(abbr=><Link key={abbr} className="border border-line rounded-lg p-2 text-sm" to={`/teams/${abbr}`}>{teams[abbr] ? `${teams[abbr].city} ${teams[abbr].name}` : abbr}</Link>)}
      {favorites.players.map(id=><Link key={id} className="border border-line rounded-lg p-2 text-sm" to={`/players/${id}`}>{players.data?.find(p=>p.id===id)?.name ?? `Player #${id}`}</Link>)}
    </div>}
    {players.error && <p className="text-sm text-muted">Player names unavailable <button onClick={players.retry}>Retry</button></p>}
  </section>;
}
