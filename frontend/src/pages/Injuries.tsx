import { useInjuries } from "../hooks/useInjuries";
import { useTeams } from "../hooks/useTeams";
import { useState } from "react";
import TeamLogo from "../components/teams/TeamLogo";
import { LoadingState, ErrorState } from "../components/ui/PageState";

type StatusFilter = "all" | "Out" | "Doubtful" | "Questionable" | "Day-to-Day";

// Цвета-токены (var) — переключаются вместе с темой
const statusColors: Record<string, { bg: string; text: string }> = {
  Out: { bg: "var(--color-danger-bg)", text: "var(--color-danger-fg)" },
  Doubtful: { bg: "var(--color-warn-bg)", text: "var(--color-warn-fg)" },
  Questionable: { bg: "var(--color-accent-bg)", text: "var(--color-accent-fg)" },
  "Day-to-Day": { bg: "var(--color-violet-bg)", text: "var(--color-violet-fg)" },
};

export default function Injuries() {
  const { injuries, loading, error } = useInjuries();
  const { teams, loading: teamsLoading } = useTeams();
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [search, setSearch] = useState("");

  const filtered = injuries.filter((i) => {
    const matchStatus = filter === "all" || i.status === filter;
    const matchSearch =
      i.playerName.toLowerCase().includes(search.toLowerCase()) ||
      i.teamAbbr.toLowerCase().includes(search.toLowerCase()) ||
      i.injury.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  if (loading || teamsLoading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="px-6 sm:px-11 py-9 max-w-[900px] mx-auto">
      <header className="mb-7">
        <h1 className="font-display font-extrabold text-[26px] tracking-wide uppercase">
          Injury Report
        </h1>
        <p className="text-[13px] text-muted mt-1">{filtered.length} players</p>
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

        <div className="flex gap-1.5 flex-wrap">
          {(["all", "Out", "Doubtful", "Questionable", "Day-to-Day"] as StatusFilter[]).map(
            (f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3.5 py-[7px] rounded-[7px] text-[11px] font-bold tracking-wide
                            uppercase cursor-pointer transition-colors ${
                              filter === f
                                ? "bg-brand border border-brand text-white"
                                : "bg-transparent border border-line text-muted hover:border-line-strong hover:text-ink"
                            }`}
              >
                {f}
              </button>
            )
          )}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-12 text-faint">No injuries found</div>
      ) : (
        <div className="bg-surface border border-line rounded-2xl overflow-hidden
                        shadow-[var(--shadow-card)]">
          {filtered.map((injury, idx) => {
            const colors =
              statusColors[injury.status] || {
                bg: "var(--color-surface-2)",
                text: "var(--color-muted)",
              };
            return (
              <div
                key={`${injury.teamAbbr}-${injury.playerName}-${idx}`}
                className={`flex items-center px-6 py-4 ${
                  idx < filtered.length - 1 ? "border-b border-line" : ""
                }`}
              >
                <div className="w-[56px] shrink-0 flex flex-col items-center gap-1">
                  <TeamLogo
                    team={teams[injury.teamAbbr]}
                    abbr={injury.teamAbbr}
                    size={34}
                  />
                  <span className="font-display font-bold text-[11px] text-faint">
                    {injury.teamAbbr}
                  </span>
                </div>

                <div className="flex-1">
                  <div className="font-display font-bold text-base">
                    {injury.playerName}
                  </div>
                  <div className="text-[13px] text-muted">
                    {injury.position} · {injury.injury}
                  </div>
                </div>

                <span
                  className="px-3 py-1 rounded-md text-[11px] font-bold tracking-[0.5px]"
                  style={{ background: colors.bg, color: colors.text }}
                >
                  {injury.status}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
