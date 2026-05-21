import type { Game, UpcomingGame, Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";

interface Props {
  game: Game;
  team1: Team;
  team2: Team;
  onSelect?: (game: UpcomingGame) => void;
}

const WIN = "var(--color-win-fg)";
const LOSS = "var(--color-danger-fg)";
const FAINT = "var(--color-faint)";

/** Компактная карточка матча для сетки расписания (3 в ряд). */
export default function ScheduleCard({ game, team1, team2, onSelect }: Props) {
  if (!team1 || !team2) return null;

  const isPast = "score1" in game;
  const clickable = !isPast && !!onSelect;

  // значение справа от каждой команды (счёт или % победы) + его цвет
  let v1: string, v2: string, c1: string, c2: string, status: string;
  if ("score1" in game) {
    v1 = String(game.score1);
    v2 = String(game.score2);
    c1 = game.score1 > game.score2 ? WIN : game.score1 < game.score2 ? LOSS : FAINT;
    c2 = game.score2 > game.score1 ? WIN : game.score2 < game.score1 ? LOSS : FAINT;
    status = "Final";
  } else {
    v1 = `${game.win1.toFixed(1)}%`;
    v2 = `${(100 - game.win1).toFixed(1)}%`;
    c1 = team1.accent;
    c2 = team2.accent;
    status = game.time;
  }

  const teamLine = (team: Team, abbr: string, value: string, color: string) => (
    <div className="flex items-center gap-2.5 min-w-0">
      <TeamLogo team={team} abbr={abbr} size={28} />
      <span className="font-display font-bold text-[15px] flex-1 truncate text-ink">
        {team.name}
      </span>
      <span
        className="font-display font-extrabold text-[19px] shrink-0"
        style={{ color }}
      >
        {value}
      </span>
    </div>
  );

  return (
    <div
      onClick={() => clickable && onSelect!(game as UpcomingGame)}
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
      onKeyDown={(e) => {
        if (clickable && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault();
          onSelect!(game as UpcomingGame);
        }
      }}
      className={`bg-surface border border-line rounded-2xl p-4 flex flex-col gap-3
                  shadow-[var(--shadow-card)] transition-all duration-200
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40 ${
                    clickable
                      ? "cursor-pointer hover:-translate-y-0.5 hover:border-line-strong " +
                        "hover:shadow-[var(--shadow-card-hover)]"
                      : ""
                  }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold tracking-wide uppercase text-faint">
          {status}
        </span>
        {game.seasonType === "playoffs" && (
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-[0.5px]
                           bg-warn-bg text-warn-fg uppercase">
            PO
          </span>
        )}
      </div>

      <div className="flex flex-col gap-2">
        {teamLine(team1, game.team1, v1, c1)}
        {teamLine(team2, game.team2, v2, c2)}
      </div>
    </div>
  );
}
