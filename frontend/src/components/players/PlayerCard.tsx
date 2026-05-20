import type { Player, Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";

interface Props {
  player: Player;
  team?: Team;
  onClick: (id: number) => void;
}

const statItems = [
  { key: "pts" as const, label: "PPG", color: "#C8102E" },
  { key: "reb" as const, label: "RPG", color: "#1E40AF" },
  { key: "ast" as const, label: "APG", color: "#059669" },
];

export default function PlayerCard({ player, team, onClick }: Props) {
  const fallbackTeam: Team = {
    abbr: player.teamAbbr,
    name: "",
    city: "",
    color: "#1C2235",
    accent: "#4A7FD4",
    record: "0-0",
  };

  const t = team || fallbackTeam;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onClick(player.id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick(player.id);
        }
      }}
      className="bg-surface border border-line rounded-2xl px-6 py-5 cursor-pointer
                 shadow-[var(--shadow-card)] transition-all duration-200
                 hover:bg-hover hover:border-line-strong hover:-translate-y-0.5
                 hover:shadow-[var(--shadow-card-hover)]
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40"
    >
      <div className="flex items-center gap-3.5 mb-4">
        <TeamLogo team={t} abbr={player.teamAbbr} size={44} />
        <div className="flex-1">
          <div className="font-display font-extrabold text-xl">
            {player.name}
          </div>
          <div className="text-[13px] text-muted mt-0.5">
            {player.position}
            {player.jerseyNumber ? ` · #${player.jerseyNumber}` : ""}
            <span className="ml-2 text-faint">{player.teamAbbr}</span>
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        {statItems.map(({ key, label, color }) => (
          <div
            key={key}
            className="flex-1 text-center py-2.5 bg-surface-2 rounded-lg"
          >
            <div
              className="font-display font-extrabold text-[22px]"
              style={{ color }}
            >
              {player[key].toFixed(1)}
            </div>
            <div className="text-[10px] font-bold tracking-wide text-faint uppercase mt-0.5">
              {label}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 text-[11px] text-faint text-right font-semibold">
        {player.gamesPlayed} GP · {player.mins.toFixed(1)} MPG
      </div>
    </div>
  );
}
