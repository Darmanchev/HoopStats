import { useFavorites } from "../../hooks/useFavorites";
export default function FavoriteButton({ team, player, name }: {team?: string; player?: number; name: string}) {
  const favorites = useFavorites();
  const selected = team ? favorites.teams.includes(team) : player !== undefined && favorites.players.includes(player);
  return <button type="button" aria-label={`${selected ? "Remove" : "Save"} ${name} ${selected ? "from" : "to"} favorites`} aria-pressed={selected}
    className="px-3 py-2 rounded-lg border border-line text-sm text-ink bg-surface hover:bg-hover"
    onKeyDown={event => event.stopPropagation()}
    onClick={event => { event.stopPropagation(); if (team) favorites.toggleTeam(team); else if (player !== undefined) favorites.togglePlayer(player); }}>
    {selected ? "★ Saved" : "☆ Save"}
  </button>;
}
