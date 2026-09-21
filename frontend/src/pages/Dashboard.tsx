import { useState } from "react";
import { useNavigate } from "react-router-dom";

import FeaturedGameWidget from "../components/dashboard/FeaturedGameWidget";
import LiveGameStatsWidget from "../components/dashboard/LiveGameStatsWidget";
import StandingsWidget from "../components/dashboard/StandingsWidget";
import TeamEfficiencyChart from "../components/dashboard/TeamEfficiencyChart";
import TopPlayerWidget from "../components/dashboard/TopPlayerWidget";
import UpcomingGamesWidget from "../components/dashboard/UpcomingGamesWidget";
import { LoadingState } from "../components/ui/PageState";
import { useDashboard } from "../hooks/useDashboard";

export default function Dashboard() {
  const navigate = useNavigate();
  const [efficiencyTeam, setEfficiencyTeam] = useState<string | null>(null);
  const {
    teams,
    upcoming,
    leaders,
    featuredGame,
    boxScore,
    initialLoading,
    refreshing,
    errors,
    lastUpdated,
    refresh,
  } = useDashboard();

  if (initialLoading) return <LoadingState />;

  const upcomingList = upcoming.slice(0, 3);
  const topPlayer = leaders.pts?.[0] ?? Object.values(leaders)[0]?.[0] ?? null;
  const hasRefreshWarning = Object.keys(errors).length > 0;
  const efficiencyCandidates = Object.values(teams)
    .filter((team) => (team.stats?.lastScores.length ?? 0) > 0)
    .sort((left, right) => (
      (left.conferenceRank ?? Number.MAX_SAFE_INTEGER)
      - (right.conferenceRank ?? Number.MAX_SAFE_INTEGER)
    ));
  const featuredEfficiencyTeam = featuredGame
    ? [featuredGame.team1, featuredGame.team2].find(
        (abbr) => (teams[abbr]?.stats?.lastScores.length ?? 0) > 0,
      )
    : undefined;
  const selectedEfficiencyTeam = efficiencyTeam
    ?? featuredEfficiencyTeam
    ?? efficiencyCandidates[0]?.abbr
    ?? null;

  return (
    <div className="max-w-[1300px] mx-auto pb-10">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="font-display font-semibold text-[26px] text-ink">NBA Analytics Overview</h1>
          <p className="mt-1 text-[12px] text-muted" aria-live="polite">
            {refreshing
              ? "Updating…"
              : lastUpdated
                ? `Last updated ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
                : "Waiting for the first update"}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void refresh()}
          disabled={refreshing}
          className="self-start rounded-full border border-line px-4 py-2 text-[12px] font-semibold text-ink transition-colors hover:bg-surface-2 disabled:cursor-wait disabled:opacity-60 sm:self-auto"
        >
          Refresh data
        </button>
      </div>

      {hasRefreshWarning && (
        <div
          role="status"
          className="mb-5 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-[13px] text-amber-900"
        >
          Some data could not be refreshed. Showing the latest available information.
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_1fr_380px] gap-6">
        <div className="h-auto xl:h-[300px]">
          <UpcomingGamesWidget
            games={upcomingList}
            teams={teams}
            onPreview={(gameId) => navigate(`/match/${gameId}`)}
          />
        </div>
        <div className="h-auto xl:h-[300px]">
          <FeaturedGameWidget
            game={featuredGame}
            team1={featuredGame ? teams[featuredGame.team1] ?? null : null}
            team2={featuredGame ? teams[featuredGame.team2] ?? null : null}
            onOpen={(gameId) => navigate(`/match/${gameId}`)}
          />
        </div>
        <div className="h-auto xl:h-[300px]">
          <TopPlayerWidget
            player={topPlayer}
            onOpen={(playerId) => navigate(`/players/${playerId}`)}
          />
        </div>

        <div className="xl:col-span-2 flex flex-col gap-6">
          <div className="h-[320px]">
            <StandingsWidget teams={teams} />
          </div>
          <div className="h-[280px]">
            <TeamEfficiencyChart
              teams={teams}
              selectedAbbr={selectedEfficiencyTeam}
              onSelect={setEfficiencyTeam}
              onOpen={(teamAbbr) => navigate(`/teams/${teamAbbr}`)}
            />
          </div>
        </div>

        <div className="h-full">
          <LiveGameStatsWidget game={featuredGame} players={boxScore} />
        </div>
      </div>
    </div>
  );
}
