import { useParams, useNavigate } from "react-router-dom";
import TeamLogo from "../components/teams/TeamLogo";
import FormBadge from "../components/teams/FormBadge";
import SparkLine from "../components/teams/SparkLine";
import { LoadingState } from "../components/ui/PageState";
import { useTeamDetail } from "../hooks/useTeamDetail";

export default function TeamDetail() {
  const { abbr } = useParams<{ abbr: string }>();
  const navigate = useNavigate();
  const { team, stats, loading, error } = useTeamDetail(abbr);

  if (loading) return <LoadingState />;

  if (error || !team) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4 px-6 text-center">
        <div className="text-sm text-brand">{error || "Team not found"}</div>
        <button
          onClick={() => navigate("/teams")}
          className="px-6 py-2.5 bg-brand text-white text-sm font-semibold rounded-lg
                     cursor-pointer border-none hover:opacity-90 transition-opacity"
        >
          Back to Teams
        </button>
      </div>
    );
  }

  const wins = parseInt(team.record.split("-")[0]) || 0;
  const losses = parseInt(team.record.split("-")[1]) || 0;
  const winPct =
    wins + losses > 0 ? ((wins / (wins + losses)) * 100).toFixed(1) : "0.0";

  return (
    <div className="px-6 sm:px-11 py-9 max-w-[800px] mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate("/teams")}
        className="flex items-center gap-1.5 text-[13px] text-muted cursor-pointer mb-7
                   bg-transparent border-none p-0 hover:text-ink transition-colors"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
          <path d="M19 12H5M12 5l-7 7 7 7" />
        </svg>
        Back to Teams
      </button>

      {/* Header */}
      <div className="bg-surface border border-line shadow-[var(--shadow-card)] rounded-2xl px-10 py-8 mb-5 flex items-center gap-6">
        <TeamLogo team={team} abbr={team.abbr} size={80} />
        <div>
          <div className="font-display font-extrabold text-[32px]">
            {team.city} {team.name}
          </div>
          <div className="text-base text-muted mt-1">
            {team.record} · {winPct}%
          </div>
        </div>
      </div>

      {/* Form & sparkline */}
      {stats && stats.form.length > 0 ? (
        <div className="bg-surface border border-line shadow-[var(--shadow-card)] rounded-xl px-7 py-6 mb-5">
          <div className="text-[11px] tracking-[1.2px] text-faint font-bold uppercase mb-3">
            Last 5 Games
          </div>
          <div className="flex gap-2 mb-6">
            {stats.form.map((r, i) => (
              <FormBadge key={i} r={r as "W" | "L"} />
            ))}
          </div>

          <div className="text-[11px] tracking-[1.2px] text-faint font-bold uppercase mb-3">
            Points — Last 10 Games
          </div>
          <SparkLine
            data={[...stats.lastScores].reverse()}
            color={team.accent}
            width={600}
            height={92}
            showValues
          />
        </div>
      ) : (
        <div className="bg-surface border border-line shadow-[var(--shadow-card)] rounded-xl px-7 py-6 text-center text-faint">
          No stats available yet
        </div>
      )}
    </div>
  );
}
