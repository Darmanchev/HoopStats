import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import type { UpcomingGame } from "../types";
import { useGames } from "../hooks/useGames";
import { useTeams } from "../hooks/useTeams";
import GameCard from "../components/matches/GameCard";
import { LoadingState, ErrorState } from "../components/ui/PageState";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

function dayHeading(dateStr: string): string {
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return `${DAYS[d.getDay()]} · ${MONTHS[d.getMonth()]} ${d.getDate()}`;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { upcoming, loading: gamesLoading, error: gamesError } = useGames();
  const { teams, loading: teamsLoading, error: teamsError } = useTeams();

  const today = upcoming.filter((g) => g.isToday);
  const future = upcoming.filter((g) => !g.isToday);

  // предстоящие игры — группируем по дням (хронологически)
  const futureByDay = useMemo(() => {
    const groups: Record<string, UpcomingGame[]> = {};
    [...future]
      .sort((a, b) => (a.date < b.date ? -1 : 1))
      .forEach((g) => {
        (groups[g.date] ||= []).push(g);
      });
    return groups;
  }, [future]);

  if (gamesLoading || teamsLoading) return <LoadingState />;
  if (gamesError || teamsError)
    return <ErrorState message={gamesError || teamsError || ""} />;

  return (
    <div className="px-6 sm:px-11 py-9 max-w-[860px] mx-auto">
      <header className="mb-7">
        <h1 className="font-display font-extrabold text-[26px] tracking-wide uppercase">
          Tonight's Games
        </h1>
        <p className="text-[13px] text-muted mt-1">
          {today.length} {today.length === 1 ? "game" : "games"} today · NBA Playoffs
        </p>
      </header>

      {today.length > 0 ? (
        <div className="flex flex-col gap-3.5 mb-11">
          {today.map((g) => (
            <GameCard
              key={g.id}
              game={g}
              team1={teams[g.team1]}
              team2={teams[g.team2]}
              onClick={() => navigate(`/match/${g.id}`)}
            />
          ))}
        </div>
      ) : (
        <div className="text-faint text-sm mb-11">No games scheduled today.</div>
      )}

      {/* предстоящие игры — отдельный заголовок на каждый день */}
      {Object.entries(futureByDay).map(([day, games]) => (
        <div key={day} className="mb-8">
          <div className="font-display font-bold text-sm tracking-wide text-faint uppercase mb-3.5">
            {dayHeading(day)}
          </div>
          <div className="flex flex-col gap-3">
            {games.map((g) => (
              <GameCard
                key={g.id}
                game={g}
                team1={teams[g.team1]}
                team2={teams[g.team2]}
                onClick={() => navigate(`/match/${g.id}`)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
