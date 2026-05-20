import { useNavigate } from "react-router-dom";
import { useAllTeams } from "../hooks/useAllTeams";
import TeamCard from "../components/teams/TeamCard";
import { LoadingState, ErrorState } from "../components/ui/PageState";
import { useState } from "react";

type SortBy = "name" | "record" | "abbr";

export default function Teams() {
  const navigate = useNavigate();
  const { teams, stats, loading, error } = useAllTeams();
  const [sortBy, setSortBy] = useState<SortBy>("record");
  const [search, setSearch] = useState("");

  const sorted = [...teams].sort((a, b) => {
    if (sortBy === "record") {
      const wa = parseInt(a.record.split("-")[0]) || 0;
      const wb = parseInt(b.record.split("-")[0]) || 0;
      return wb - wa;
    }
    if (sortBy === "name") return a.name.localeCompare(b.name);
    return a.abbr.localeCompare(b.abbr);
  });

  const filtered = sorted.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.city.toLowerCase().includes(search.toLowerCase()) ||
      t.abbr.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="px-6 sm:px-11 py-9 max-w-[1100px] mx-auto">
      <header className="mb-7">
        <h1 className="font-display font-extrabold text-[26px] tracking-wide uppercase">
          NBA Teams
        </h1>
        <p className="text-[13px] text-muted mt-1">{filtered.length} teams</p>
      </header>

      <div className="flex gap-3 mb-6 items-center flex-wrap">
        <input
          type="text"
          placeholder="Search teams..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3.5 py-2 rounded-lg border border-line bg-surface text-ink text-sm w-60
                     outline-none placeholder:text-faint focus:border-brand transition-colors"
        />

        <div className="flex gap-1.5">
          {(["record", "name", "abbr"] as SortBy[]).map((s) => (
            <button
              key={s}
              onClick={() => setSortBy(s)}
              className={`px-3.5 py-[7px] rounded-[7px] text-[11px] font-bold tracking-wide
                          uppercase cursor-pointer transition-colors ${
                            sortBy === s
                              ? "bg-brand border border-brand text-white"
                              : "bg-transparent border border-line text-muted hover:border-line-strong hover:text-ink"
                          }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3.5">
        {filtered.map((team) => (
          <TeamCard
            key={team.abbr}
            team={team}
            stats={stats[team.abbr]}
            onClick={(abbr) => navigate(`/teams/${abbr}`)}
          />
        ))}
      </div>
    </div>
  );
}
