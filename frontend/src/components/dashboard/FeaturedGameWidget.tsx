import type { LiveGame, UpcomingGame, Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";

interface Props {
  game: LiveGame | UpcomingGame | null;
  team1: Team | null;
  team2: Team | null;
  onOpen?: (gameId: string) => void;
}

function isLiveGame(game: LiveGame | UpcomingGame): game is LiveGame {
  return "status" in game;
}

export default function FeaturedGameWidget({ game, team1, team2, onOpen = () => undefined }: Props) {
  if (!game || !team1 || !team2) {
    return (
      <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line h-full flex items-center justify-center">
        <span className="text-faint text-sm">No featured game</span>
      </div>
    );
  }

  const liveGame = isLiveGame(game) ? game : null;
  const status = liveGame?.status ?? "scheduled";
  const hasScore = liveGame?.score1 != null && liveGame.score2 != null;
  const statusLabel = status === "live"
    ? liveGame?.statusText || `Q${liveGame?.period ?? ""} ${liveGame?.clock ?? ""}`.trim()
    : status === "final"
      ? "Final"
      : "Scheduled";

  return (
    <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line flex flex-col h-full">
      <div className="mb-6">
        <h2 className="font-display font-semibold text-[18px] text-ink">Featured Game:</h2>
        <p className="text-[14px] text-muted">{team1.city} {team1.name} vs. {team2.city} {team2.name}</p>
      </div>

      <div className="flex-1 flex flex-col justify-center">
        <div className="flex items-center justify-center gap-6 mb-6">
          <TeamLogo team={team1} abbr={game.team1} size={50} />
          <div className="font-display font-bold text-[42px] tracking-tight text-ink text-center">
            {hasScore ? `${liveGame.score1} - ${liveGame.score2}` : game.time}
          </div>
          <TeamLogo team={team2} abbr={game.team2} size={50} />
        </div>

        <div className="w-full">
          <div className="flex justify-between items-center mb-2">
            <span className="text-[12px] font-medium text-ink">
              {status === "live" ? "Live" : status === "final" ? "Completed" : game.venue || "Venue TBA"}
            </span>
            <span className="text-[12px] font-bold text-ink">{statusLabel}</span>
          </div>
          <div className="h-2 w-full bg-surface-2 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand transition-all"
              style={{ width: `${game.win1 ?? 50}%` }}
            />
          </div>
          {status === "scheduled" && game.prediction && (
            <p className="mt-2 text-center text-[12px] text-muted">Prediction: {game.prediction}</p>
          )}
        </div>
      </div>

      <div className="mt-6">
        <button
          type="button"
          onClick={() => onOpen(game.id)}
          className="w-full py-2.5 rounded-full border-2 border-brand text-brand font-semibold text-[14px] hover:bg-brand/5 transition-colors"
        >
          {status === "live" ? "Live Stats" : "Game Details"}
        </button>
      </div>
    </div>
  );
}
