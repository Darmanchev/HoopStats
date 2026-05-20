import type { UpcomingGame, Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";
import WinBar from "./WinBar";

interface Props {
  game: UpcomingGame;
  team1: Team;
  team2: Team;
  onClick: (game: UpcomingGame) => void;
}

export default function GameCard({ game, team1, team2, onClick }: Props) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onClick(game)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick(game);
        }
      }}
      className="bg-surface border border-line rounded-2xl px-7 py-[22px] cursor-pointer
                 shadow-[var(--shadow-card)] transition-all duration-200
                 hover:bg-hover hover:border-line-strong hover:-translate-y-0.5
                 hover:shadow-[var(--shadow-card-hover)]
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40"
    >
      <div className="flex justify-between items-center mb-[18px]">
        <span className="text-[11px] font-bold tracking-wide uppercase text-info">
          {game.date} · {game.time}
        </span>
        <span className="text-[11px] text-faint">{game.venue}</span>
      </div>

      <div className="flex items-center gap-4 mb-5">
        <TeamLogo team={team1} abbr={game.team1} size={46} />
        <div className="flex-1">
          <div className="font-display font-bold text-[19px] leading-[1.1]">
            {team1.city} <span style={{ color: team1.accent }}>{team1.name}</span>
          </div>
          <div className="text-xs text-muted mt-[3px]">{team1.record}</div>
        </div>

        <span className="font-display font-extrabold text-base text-line-strong tracking-[3px]">
          VS
        </span>

        <div className="flex-1 text-right">
          <div className="font-display font-bold text-[19px] leading-[1.1]">
            <span style={{ color: team2.accent }}>{team2.name}</span> {team2.city}
          </div>
          <div className="text-xs text-muted mt-[3px]">{team2.record}</div>
        </div>
        <TeamLogo team={team2} abbr={game.team2} size={46} />
      </div>

      <WinBar pct1={game.win1} team1={team1} team2={team2} />
    </div>
  );
}
