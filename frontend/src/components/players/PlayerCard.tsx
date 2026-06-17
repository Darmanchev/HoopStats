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

// Официальный CDN NBA с фото игроков (ключ — nbaId)
const HEADSHOT_URL = (nbaId: number) =>
  `https://cdn.nba.com/headshots/nba/latest/1040x760/${nbaId}.png`;

export default function PlayerCard({ player, team, onClick }: Props) {
  const fallbackTeam: Team = {
    abbr: player.teamAbbr,
    name: "",
    city: "",
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
      className="relative overflow-hidden flex bg-surface border border-line rounded-2xl
                 cursor-pointer shadow-[var(--shadow-card)] transition-all duration-200
                 hover:bg-hover hover:border-line-strong hover:-translate-y-0.5
                 hover:shadow-[var(--shadow-card-hover)]
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40"
    >
      {/* ЛЕВО — имя и статистика */}
      <div className="flex-1 min-w-0 p-5">
        <div className="flex items-center gap-3 mb-4">
          <TeamLogo team={t} abbr={player.teamAbbr} size={38} />
          <div className="min-w-0">
            <div className="font-display font-extrabold text-lg leading-tight truncate">
              {player.name}
            </div>
            <div className="text-[12px] text-muted mt-0.5 truncate">
              {player.position}
              {player.jerseyNumber ? ` · #${player.jerseyNumber}` : ""}
              <span className="ml-1.5 text-faint">{player.teamAbbr}</span>
            </div>
          </div>
        </div>

        {/* 3 статы — вертикально */}
        <div className="flex flex-col gap-1">
          {statItems.map(({ key, label, color }) => (
            <div key={key} className="flex items-baseline gap-2">
              <span
                className="font-display font-extrabold text-[22px] w-[52px] text-right"
                style={{ color }}
              >
                {player[key].toFixed(1)}
              </span>
              <span className="text-[10px] font-bold tracking-wide text-faint uppercase">
                {label}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-3 text-[11px] text-faint font-semibold">
          {player.gamesPlayed} GP · {player.mins.toFixed(1)} MPG
        </div>
      </div>

      {/* ПРАВО — фото игрока в отдельной колонке */}
      <div className="w-[122px] shrink-0 relative">
        <img
          src={HEADSHOT_URL(player.nbaId)}
          alt={player.name}
          loading="lazy"
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
          className="absolute inset-0 w-full h-full object-cover object-top
                     select-none pointer-events-none
                     [mask-image:linear-gradient(to_right,transparent,#000_38%)]"
        />
      </div>
    </div>
  );
}
