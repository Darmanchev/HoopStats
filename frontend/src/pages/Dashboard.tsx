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
    boxScoreGame,
    boxScore,
    initialLoading,
    refreshing,
    errors,
    lastUpdated,
    refresh,
    selectedSeason,
    setSelectedSeason,
    seasonData,
    sourceStatus,
    importedSeasons = [],
  } = useDashboard();

  if (initialLoading) return <LoadingState />;

  const upcomingList = upcoming.slice(0, 3);
  const displayLeaders = seasonData?.leaders ?? (selectedSeason ? {} : leaders);
  const topPlayer = displayLeaders.pts?.[0] ?? Object.values(displayLeaders)[0]?.[0] ?? null;
  const standingsTeams = seasonData ? Object.fromEntries(seasonData.teams.map((team) => [team.abbr, team])) : {};
  const statsTeams = seasonData ? standingsTeams : teams;
  const hasRefreshWarning = Object.keys(errors).length > 0;
  const efficiencyCandidates = Object.values(statsTeams)
    .filter((team) => (team.stats?.lastScores.length ?? 0) > 0)
    .sort((left, right) => (
      (left.conferenceRank ?? Number.MAX_SAFE_INTEGER)
      - (right.conferenceRank ?? Number.MAX_SAFE_INTEGER)
    ));
  const featuredEfficiencyTeam = featuredGame
    ? [featuredGame.team1, featuredGame.team2].find(
        (abbr) => (statsTeams[abbr]?.stats?.lastScores.length ?? 0) > 0,
      )
    : undefined;
  const selectedEfficiencyTeam = (efficiencyTeam && statsTeams[efficiencyTeam]?.stats?.lastScores.length ? efficiencyTeam : null)
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
                ? `Last checked ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
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

      <div className="mb-5 flex flex-wrap items-center gap-3">
        <label htmlFor="dashboard-season" className="text-sm text-muted">Statistics season</label>
        <select id="dashboard-season" value={selectedSeason ?? ""} onChange={(event) => setSelectedSeason(event.target.value || undefined)} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink">
          <option value="">Latest available statistics</option>
          {importedSeasons.map((season) => <option key={season} value={season}>{season}</option>)}
        </select>
        {seasonData?.season && <span className="text-xs text-muted">{seasonData.season} · records based on imported games</span>}
      </div>

      {Object.entries(sourceStatus ?? {}).length > 0 && <details className="mb-5 text-xs text-muted">
        <summary className="cursor-pointer">Source update status</summary>
        <div className="mt-2 flex flex-col gap-1">
          {Object.entries(sourceStatus).map(([name, status]) => <p key={name}>
            {name.replace(/^sync_/, "").replaceAll("_", " ")}: {status.state === "failed" ? "Update failed" : status.state === "running" ? "Updating" : "Updated"}
            {status.last_success ? ` · Last successful import ${new Date(status.last_success).toLocaleString()}` : " · No successful import recorded"}
          </p>)}
        </div>
      </details>}

      {hasRefreshWarning && (
        <div
          role="status"
          className="mb-5 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-[13px] text-amber-900"
        >
          Some data could not be refreshed. Showing the latest available information.
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="min-w-0 xl:min-h-[420px]">
          <UpcomingGamesWidget
            games={upcomingList}
            teams={teams}
            onPreview={(gameId) => navigate(`/match/${gameId}`)}
          />
        </div>
        <div className="min-w-0 xl:min-h-[420px]">
          <FeaturedGameWidget
            game={featuredGame}
            team1={featuredGame ? teams[featuredGame.team1] ?? null : null}
            team2={featuredGame ? teams[featuredGame.team2] ?? null : null}
            onOpen={(gameId) => navigate(`/match/${gameId}`)}
          />
        </div>
        <div className="min-w-0 xl:min-h-[420px]">
          <TopPlayerWidget
            player={topPlayer}
            season={seasonData?.season ?? undefined}
            error={errors.leaders || errors.seasonData}
            imported={seasonData?.playersAvailable}
            onOpen={(playerId) => navigate(`/players/${playerId}${topPlayer?.season ? `?season=${encodeURIComponent(topPlayer.season)}` : ""}`)}
          />
        </div>

        <div className="xl:col-span-2 flex flex-col gap-6">
          <div className="h-[320px]">
            {!seasonData?.teamsAvailable && seasonData ? <div className="bg-surface rounded-3xl p-6 h-full flex items-center justify-center text-muted">No team games imported for {seasonData.season ?? "a season"}</div> : <StandingsWidget teams={seasonData ? standingsTeams : teams} />}
          </div>
          <div className="h-[280px]">
            <TeamEfficiencyChart
              teams={statsTeams}
              selectedAbbr={selectedEfficiencyTeam}
              onSelect={setEfficiencyTeam}
              onOpen={(teamAbbr) => navigate(`/teams/${teamAbbr}${seasonData?.season ? `?season=${encodeURIComponent(seasonData.season)}` : ""}`)}
            />
          </div>
        </div>

        <div className="h-full">
          <LiveGameStatsWidget game={boxScoreGame} players={boxScore} error={errors.boxScore || errors.today || (sourceStatus?.sync_box_scores?.state === "failed" ? "Box-score provider update failed" : undefined)} />
        </div>
      </div>
    </div>
  );
}
