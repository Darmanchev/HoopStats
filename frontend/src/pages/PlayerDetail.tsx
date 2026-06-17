import { useParams, useNavigate } from "react-router-dom";
import type { PlayerDetail } from "../types";
import TeamLogo from "../components/teams/TeamLogo";
import { LoadingState } from "../components/ui/PageState";
import { usePlayerDetail } from "../hooks/usePlayerDetail";

const statCategories = [
  { key: "pts",  label: "Points",   sub: "PPG", color: "#C8102E" },
  { key: "reb",  label: "Rebounds", sub: "RPG", color: "#1E40AF" },
  { key: "ast",  label: "Assists",  sub: "APG", color: "#059669" },
  { key: "stl",  label: "Steals",   sub: "SPG", color: "#92400E" },
  { key: "blk",  label: "Blocks",   sub: "BPG", color: "#5B21B6" },
  { key: "mins", label: "Minutes",  sub: "MPG", color: "#4A7FD4" },
];

const shootingStats = [
  { key: "fgPct",  label: "FG%", color: "#C8102E" },
  { key: "fg3Pct", label: "3P%", color: "#1E40AF" },
  { key: "ftPct",  label: "FT%", color: "#059669" },
];

export default function PlayerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { player, loading, error } = usePlayerDetail(id);

  if (loading) return <LoadingState />;

  if (error || !player) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4 px-6 text-center">
        <div className="text-sm text-brand">{error || "Player not found"}</div>
        <button
          onClick={() => navigate("/players")}
          className="px-6 py-2.5 bg-brand text-white text-sm font-semibold rounded-lg
                     cursor-pointer border-none hover:opacity-90 transition-opacity"
        >
          Back to Players
        </button>
      </div>
    );
  }

  const teamFallback = {
    abbr: player.teamAbbr,
    name: player.teamName || "",
    city: player.teamCity || "",
    record: "0-0",
  };

  return (
    <div className="px-6 sm:px-11 py-9 max-w-[800px] mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate("/players")}
        className="flex items-center gap-1.5 text-[13px] text-muted cursor-pointer mb-7
                   bg-transparent border-none p-0 hover:text-ink transition-colors"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
          <path d="M19 12H5M12 5l-7 7 7 7" />
        </svg>
        Back to Players
      </button>

      {/* Header */}
      <div className="bg-surface border border-line shadow-[var(--shadow-card)] rounded-2xl px-10 py-8 mb-5 flex items-center gap-6">
        <TeamLogo team={teamFallback} abbr={player.teamAbbr} size={80} />
        <div>
          <div className="font-display font-extrabold text-[32px]">{player.name}</div>
          <div className="text-base text-muted mt-1">
            {player.position}
            {player.jerseyNumber ? ` · #${player.jerseyNumber}` : ""}
            <span className="ml-3">{player.teamCity} {player.teamName}</span>
          </div>
          <div className="text-[13px] text-faint mt-1">{player.gamesPlayed} Games Played</div>
        </div>
      </div>

      {/* Per-game averages */}
      <div className="bg-surface border border-line shadow-[var(--shadow-card)] rounded-xl px-7 py-6 mb-5">
        <div className="text-[11px] tracking-[1.2px] text-faint font-bold uppercase mb-4">
          Per Game Averages
        </div>
        <div className="grid grid-cols-3 gap-3">
          {statCategories.map(({ key, label, sub, color }) => (
            <div key={key} className="text-center py-4 bg-surface-2 rounded-xl">
              <div className="font-display font-extrabold text-[28px]" style={{ color }}>
                {(player[key as keyof PlayerDetail] as number)?.toFixed?.(1) ?? "0.0"}
              </div>
              <div className="text-[10px] font-bold tracking-[1px] text-faint uppercase mt-1">
                {label}
              </div>
              <div className="text-[11px] text-faint">{sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Shooting splits */}
      <div className="bg-surface border border-line shadow-[var(--shadow-card)] rounded-xl px-7 py-6 mb-5">
        <div className="text-[11px] tracking-[1.2px] text-faint font-bold uppercase mb-4">
          Shooting
        </div>
        <div className="grid grid-cols-3 gap-3">
          {shootingStats.map(({ key, label, color }) => {
            const val = player[key as keyof PlayerDetail] as number;
            const pct = (val * 100).toFixed(1);
            return (
              <div key={key} className="text-center py-4 bg-surface-2 rounded-xl">
                <div className="font-display font-extrabold text-[28px]" style={{ color }}>
                  {pct}%
                </div>
                <div className="text-[10px] font-bold tracking-[1px] text-faint uppercase mt-1">
                  {label}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
