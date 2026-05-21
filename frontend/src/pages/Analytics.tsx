import type { Player } from "../types";
import { useAnalytics } from "../hooks/useAnalytics";
import { useTeams } from "../hooks/useTeams";
import TeamLogo from "../components/teams/TeamLogo";
import { LoadingState, ErrorState } from "../components/ui/PageState";

type StatKey = "pts" | "reb" | "ast" | "fgPct";

const LEADER_CARDS: {
  key: StatKey;
  title: string;
  color: string;
  pct?: boolean;
}[] = [
  { key: "pts", title: "Points · PPG", color: "#C8102E" },
  { key: "reb", title: "Rebounds · RPG", color: "#1E40AF" },
  { key: "ast", title: "Assists · APG", color: "#059669" },
  { key: "fgPct", title: "Field Goal %", color: "#7C3AED", pct: true },
];

function LeaderCard({
  title,
  color,
  players,
  statKey,
  pct,
}: {
  title: string;
  color: string;
  players: Player[];
  statKey: StatKey;
  pct?: boolean;
}) {
  return (
    <div className="bg-surface border border-line rounded-2xl shadow-[var(--shadow-card)] p-5">
      <div className="text-[11px] tracking-[1.2px] text-faint font-bold uppercase mb-3.5">
        {title}
      </div>
      <div className="flex flex-col gap-2.5">
        {players.map((p, i) => {
          const val = p[statKey];
          return (
            <div key={p.id} className="flex items-center gap-2.5">
              <span className="w-4 text-xs font-bold text-faint tabular-nums">
                {i + 1}
              </span>
              <div className="flex-1 min-w-0">
                <div className="font-display font-bold text-sm truncate">
                  {p.name}
                </div>
                <div className="text-[11px] text-faint">{p.teamAbbr}</div>
              </div>
              <span
                className="font-display font-extrabold text-[18px]"
                style={{ color }}
              >
                {pct ? (val * 100).toFixed(1) : val.toFixed(1)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function Analytics() {
  const { elo, leaders, loading, error } = useAnalytics();
  const { teams, loading: teamsLoading } = useTeams();

  if (loading || teamsLoading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  const maxElo = elo.length ? Math.max(...elo.map((e) => e.elo)) : 1;
  const minElo = elo.length ? Math.min(...elo.map((e) => e.elo)) : 0;
  const span = maxElo - minElo || 1;

  return (
    <div className="px-6 sm:px-11 py-9 max-w-[1100px] mx-auto">
      <header className="mb-7">
        <h1 className="font-display font-extrabold text-[26px] tracking-wide uppercase">
          Analytics
        </h1>
        <p className="text-[13px] text-muted mt-1">
          League insights · 2025–26 season
        </p>
      </header>

      {/* Power Rankings — Elo */}
      <section className="mb-10">
        <h2 className="font-display font-bold text-base tracking-wide text-faint uppercase mb-3.5">
          Power Rankings · Elo
        </h2>
        <div className="bg-surface border border-line rounded-2xl overflow-hidden
                        shadow-[var(--shadow-card)]">
          {elo.map((e, i) => {
            const t = teams[e.teamAbbr];
            const frac = (e.elo - minElo) / span;
            return (
              <div
                key={e.teamAbbr}
                className="flex items-center gap-3 px-5 py-3 border-b border-line last:border-b-0"
              >
                <span className="w-6 text-sm font-bold text-faint tabular-nums">
                  {i + 1}
                </span>
                {t && <TeamLogo team={t} abbr={e.teamAbbr} size={26} />}
                <span className="font-display font-bold text-[15px] flex-1 truncate">
                  {t ? `${t.city} ${t.name}` : e.teamAbbr}
                </span>
                <div className="hidden sm:block w-[180px] h-2 rounded-full bg-surface-2 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-brand transition-[width] duration-500"
                    style={{ width: `${22 + frac * 78}%` }}
                  />
                </div>
                <span className="font-display font-extrabold text-[15px] w-[54px] text-right tabular-nums">
                  {e.elo}
                </span>
              </div>
            );
          })}
        </div>
      </section>

      {/* League Leaders */}
      <section>
        <h2 className="font-display font-bold text-base tracking-wide text-faint uppercase mb-3.5">
          League Leaders
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {LEADER_CARDS.map((c) => (
            <LeaderCard
              key={c.key}
              title={c.title}
              color={c.color}
              statKey={c.key}
              pct={c.pct}
              players={leaders[c.key] ?? []}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
