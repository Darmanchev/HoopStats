import { useNavigate } from "react-router-dom";
import { usePlayers } from "../hooks/usePlayers";
import { useTeams } from "../hooks/useTeams";
import PlayerCard from "../components/players/PlayerCard";
import { LoadingState, ErrorState } from "../components/ui/PageState";
import { useState } from "react";

type SortBy = "pts" | "reb" | "ast" | "games_played" | "name";
type PositionFilter = "all" | "G" | "F" | "C";

export default function Players() {
  const navigate = useNavigate();
  const { teams, loading: teamsLoading } = useTeams();
  const [sortBy, setSortBy] = useState<SortBy>("pts");
  const [positionFilter, setPositionFilter] = useState<PositionFilter>("all");
  const [search, setSearch] = useState("");
  const minGames = 10; // минимум сыгранных игр для попадания в список

  const { players, loading, error } = usePlayers({
    sortBy,
    position: positionFilter === "all" ? undefined : positionFilter,
    minGames,
    limit: 200,
  });

  const filtered = players.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.teamAbbr.toLowerCase().includes(search.toLowerCase())
  );

  if (loading || teamsLoading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  const sortOptions: { key: SortBy; label: string }[] = [
    { key: "pts", label: "PPG" },
    { key: "reb", label: "RPG" },
    { key: "ast", label: "APG" },
    { key: "games_played", label: "GP" },
    { key: "name", label: "Name" },
  ];

  const positions: { key: PositionFilter; label: string }[] = [
    { key: "all", label: "All" },
    { key: "G", label: "Guards" },
    { key: "F", label: "Forwards" },
    { key: "C", label: "Centers" },
  ];

  return (
    <div className="px-6 sm:px-11 py-9 max-w-[1100px] mx-auto">
      <header className="mb-7">
        <h1 className="font-display font-extrabold text-[26px] tracking-wide uppercase">
          Players
        </h1>
        <p className="text-[13px] text-muted mt-1">
          {filtered.length} players · {minGames}+ GP
        </p>
      </header>

      <div className="flex gap-3 mb-6 items-center flex-wrap">
        <input
          type="text"
          placeholder="Search players..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3.5 py-2 rounded-lg border border-line bg-surface text-ink text-sm w-60
                     outline-none placeholder:text-faint focus:border-brand transition-colors"
        />

        <div className="flex gap-1.5">
          {sortOptions.map((s) => (
            <button
              key={s.key}
              onClick={() => setSortBy(s.key)}
              className={`px-3.5 py-[7px] rounded-[7px] text-[11px] font-bold tracking-wide
                          uppercase cursor-pointer transition-colors ${
                            sortBy === s.key
                              ? "bg-brand border border-brand text-white"
                              : "bg-transparent border border-line text-muted hover:border-line-strong hover:text-ink"
                          }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        <div className="flex gap-1.5">
          {positions.map((p) => (
            <button
              key={p.key}
              onClick={() => setPositionFilter(p.key)}
              className={`px-3.5 py-[7px] rounded-[7px] text-[11px] font-bold tracking-wide
                          cursor-pointer transition-colors ${
                            positionFilter === p.key
                              ? "bg-info border border-info text-white"
                              : "bg-transparent border border-line text-muted hover:border-line-strong hover:text-ink"
                          }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-12 text-faint">No players found</div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-3.5">
          {filtered.map((player) => (
            <PlayerCard
              key={player.id}
              player={player}
              team={teams[player.teamAbbr]}
              onClick={(id) => navigate(`/players/${id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
