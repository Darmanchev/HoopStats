import { useNavigate } from "react-router-dom";
import { useGames } from "../hooks/useGames";
import { useTeams } from "../hooks/useTeams";
import GameCard from "../components/matches/GameCard";
import { LoadingState, ErrorState } from "../components/ui/PageState";

export default function Dashboard() {
  const navigate = useNavigate();
  const { upcoming, loading: gamesLoading, error: gamesError } = useGames();
  const { teams, loading: teamsLoading, error: teamsError } = useTeams();

  const today = upcoming.filter((g) => g.isToday);
  const future = upcoming.filter((g) => !g.isToday);

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
          April 25, 2026 · NBA Playoffs Round 1
        </p>
      </header>

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

      <div className="font-display font-bold text-sm tracking-wide text-faint uppercase mb-3.5">
        Upcoming
      </div>
      <div className="flex flex-col gap-3">
        {future.map((g) => (
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
  );
}
