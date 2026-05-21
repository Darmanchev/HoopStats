import type { Team, TeamStats } from "../../types";
import FormBadge from "../teams/FormBadge";
import TeamLogo from "../teams/TeamLogo";

interface Props {
  team: Team;
  stats?: TeamStats;
  onClick: (abbr: string) => void;
}

export default function TeamCard({ team, stats, onClick }: Props) {
  const wins = parseInt(team.record.split("-")[0]) || 0;
  const losses = parseInt(team.record.split("-")[1]) || 0;
  const winPct = wins + losses > 0 ? (wins / (wins + losses) * 100).toFixed(1) : "0.0";

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onClick(team.abbr)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick(team.abbr);
        }
      }}
      className="bg-surface border border-line rounded-2xl px-6 py-[22px] cursor-pointer
                 shadow-[var(--shadow-card)] transition-all duration-200
                 hover:-translate-y-0.5 hover:border-line-strong
                 hover:shadow-[var(--shadow-card-hover)]
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40"
    >
      <div className="flex items-center gap-3.5 mb-4">
        <TeamLogo team={team} abbr={team.abbr} size={48} />
        <div>
          <div className="font-display font-extrabold text-xl">
            {team.city} {team.name}
          </div>
          <div className="text-[13px] text-muted">
            {team.record} · {winPct}%
          </div>
        </div>
      </div>

      {stats && stats.form.length > 0 && (
        <div>
          <div className="text-[10px] tracking-[1.2px] text-faint font-bold mb-1.5">
            LAST 5
          </div>
          <div className="flex gap-[5px]">
            {stats.form.map((r: string, i: number) => (
              <FormBadge key={i} r={r as "W" | "L"} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
