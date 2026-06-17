import type { Game, UpcomingGame, Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";
import { getTeamColors } from "../../utils/colors";

interface Props {
  game: Game;
  team1: Team;
  team2: Team;
  isLast: boolean;
  onSelect?: (game: UpcomingGame) => void;
}

export default function ScheduleRow({
  game,
  team1,
  team2,
  isLast,
  onSelect,
}: Props) {
  const isPast = "score1" in game; // отличаем прошедший от предстоящего
  const clickable = !isPast && !!onSelect;

  return (
    <div
      onClick={() => clickable && onSelect!(game as UpcomingGame)}
      className={`flex items-center px-6 py-4 transition-colors ${
        isLast ? "" : "border-b border-line"
      } ${clickable ? "cursor-pointer hover:bg-hover" : "cursor-default"}`}
    >
      <div className="w-20 text-xs text-muted shrink-0">{game.date}</div>

      {game.seasonType === "playoffs" && (
        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-[0.5px]
                         bg-warn-bg text-warn-fg uppercase shrink-0">
          PO
        </span>
      )}

      <div className="flex-1 flex items-center gap-2.5 flex-wrap">
        <div className="flex items-center gap-2">
          <TeamLogo team={team1} abbr={game.team1} size={28} />
          <span className="font-display font-bold text-[15px]">
            {team1.city} {team1.name}
          </span>
        </div>
        <span className="text-[11px] text-faint">vs</span>
        <div className="flex items-center gap-2">
          <TeamLogo team={team2} abbr={game.team2} size={28} />
          <span className="font-display font-bold text-[15px]">
            {team2.city} {team2.name}
          </span>
        </div>
      </div>

      {isPast ? (
        <div className="flex items-center gap-2.5 shrink-0">
          <span
            className="font-display font-extrabold text-[22px]"
            style={{
              color:
                game.score1 > game.score2
                  ? "var(--color-win-fg)"
                  : game.score1 < game.score2
                    ? "var(--color-danger-fg)"
                    : "var(--color-faint)",
            }}
          >
            {game.score1}
          </span>
          <span className="text-faint text-sm">—</span>
          <span
            className="font-display font-extrabold text-[22px]"
            style={{
              color:
                game.score2 > game.score1
                  ? "var(--color-win-fg)"
                  : game.score2 < game.score1
                    ? "var(--color-danger-fg)"
                    : "var(--color-faint)",
            }}
          >
            {game.score2}
          </span>
          <span className="px-2 py-[3px] bg-surface-2 rounded text-[10px] font-bold
                           tracking-wide text-faint ml-1">
            FINAL
          </span>
        </div>
      ) : (
        <div className="flex items-center gap-3.5 shrink-0">
          <span className="text-[13px] font-semibold text-info">
            {game.time}
          </span>
          <div className="flex gap-1 items-center">
            <span
              className="font-display font-bold text-sm"
              style={{ color: getTeamColors(game.team1).accent }}
            >
              {game.win1}%
            </span>
            <span className="text-[11px] text-faint">·</span>
            <span
              className="font-display font-bold text-sm"
              style={{ color: getTeamColors(game.team2).accent }}
            >
              {100 - game.win1}%
            </span>
          </div>
          {onSelect && (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                 className="text-faint">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          )}
        </div>
      )}
    </div>
  );
}
