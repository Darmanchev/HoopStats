import type { UpcomingGame, Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";

interface Props {
  games: UpcomingGame[];
  teams: Record<string, Team>;
}

export default function UpcomingGamesWidget({ games, teams }: Props) {
  // Форматируем дату первой игры
  const headerDate = games.length > 0 
    ? new Date(games[0].date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
    : "No games scheduled";

  return (
    <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line flex flex-col h-full">
      <div className="mb-5">
        <h2 className="font-display font-semibold text-[18px] text-ink">Upcoming Games</h2>
        <p className="text-[13px] text-muted">{headerDate}</p>
      </div>

      <div className="flex flex-col gap-3 flex-1 overflow-y-auto">
        {games.map((g) => {
          const t1 = teams[g.team1];
          const t2 = teams[g.team2];
          if (!t1 || !t2) return null;

          return (
            <div key={g.id} className="bg-surface-2 rounded-2xl p-4 flex items-center justify-between border border-transparent hover:border-line transition-colors">
              <div className="flex flex-col items-center gap-1 w-[60px]">
                <TeamLogo team={t1} abbr={g.team1} size={36} />
                <span className="font-display font-bold text-[14px] text-ink">{g.team1}</span>
              </div>
              
              <div className="flex flex-col items-center flex-1">
                <span className="text-[13px] font-semibold text-ink">{g.time}</span>
                <span className="text-[11px] text-muted text-center leading-tight mt-0.5 max-w-[100px] truncate">{g.venue || "TBA"}</span>
                <button className="mt-2 px-4 py-1 bg-[#DCE9FD] text-[#1D4ED8] rounded-full text-[11px] font-semibold hover:bg-[#C5DAFC] transition-colors">
                  Preview
                </button>
              </div>

              <div className="flex flex-col items-center gap-1 w-[60px]">
                <TeamLogo team={t2} abbr={g.team2} size={36} />
                <span className="font-display font-bold text-[14px] text-ink">{g.team2}</span>
              </div>
            </div>
          );
        })}
        {games.length === 0 && (
          <div className="flex-1 flex items-center justify-center text-faint text-sm">
            No upcoming games.
          </div>
        )}
      </div>
    </div>
  );
}
