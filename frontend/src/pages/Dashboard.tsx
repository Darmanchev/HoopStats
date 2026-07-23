import { useGames } from "../hooks/useGames";
import { useTeams } from "../hooks/useTeams";
import { LoadingState, ErrorState } from "../components/ui/PageState";

import UpcomingGamesWidget from "../components/dashboard/UpcomingGamesWidget";
import FeaturedGameWidget from "../components/dashboard/FeaturedGameWidget";
import TopPlayerWidget from "../components/dashboard/TopPlayerWidget";
import StandingsWidget from "../components/dashboard/StandingsWidget";
import LiveGameStatsWidget from "../components/dashboard/LiveGameStatsWidget";
import TeamEfficiencyChart from "../components/dashboard/TeamEfficiencyChart";

export default function Dashboard() {
  const { upcoming, loading: gamesLoading, error: gamesError } = useGames(
    undefined,
    false
  );
  const { teams, loading: teamsLoading, error: teamsError } = useTeams();

  if (gamesLoading || teamsLoading) return <LoadingState />;
  if (gamesError || teamsError) return <ErrorState message={gamesError || teamsError || ""} />;

  // Берем ближайшие игры (не важно, сегодня они или нет)
  const upcomingList = upcoming.slice(0, 3);
  const featured = upcoming.length > 0 ? upcoming[0] : null;

  return (
    <div className="max-w-[1300px] mx-auto pb-10">
      <div className="mb-6">
        <h1 className="font-display font-semibold text-[26px] text-ink">NBA Analytics Overview</h1>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_1fr_380px] gap-6">
        
        {/* Верхний ряд */}
        <div className="h-auto xl:h-[300px]">
          <UpcomingGamesWidget games={upcomingList} teams={teams} />
        </div>
        <div className="h-auto xl:h-[300px]">
          <FeaturedGameWidget 
            game={featured} 
            team1={featured ? teams[featured.team1] : null} 
            team2={featured ? teams[featured.team2] : null} 
          />
        </div>
        <div className="h-auto xl:h-[300px]">
          <TopPlayerWidget />
        </div>

        {/* Нижний ряд: левая часть занимает 2 колонки */}
        <div className="xl:col-span-2 flex flex-col gap-6">
          <div className="h-[320px]">
            <StandingsWidget teams={teams} />
          </div>
          <div className="h-[280px]">
            <TeamEfficiencyChart />
          </div>
        </div>

        {/* Нижний ряд: правая часть занимает 1 колонку (380px) */}
        <div className="h-full">
          <LiveGameStatsWidget />
        </div>

      </div>
    </div>
  );
}
