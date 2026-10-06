import { Link, useParams } from "react-router-dom";
import TeamLogo from "../components/teams/TeamLogo";
import WinBar from "../components/matches/WinBar";
import FormBadge from "../components/teams/FormBadge";
import SparkLine from "../components/teams/SparkLine";
import { LoadingState } from "../components/ui/PageState";
import { useMatch } from "../hooks/useMatch";
import { formatGameTime } from "../utils/gameTime";
import type { Team } from "../types";

export default function MatchDetail() {
  const { id } = useParams<{id:string}>();
  const {game,teams,stats,loading,error,teamError,statsErrors,boxScore,boxLoading,boxError,sourceStatus,retry,retryTeams,retryStats,retryBox} = useMatch(id);
  if (loading) return <LoadingState/>;
  if (!game) return <div className="p-8"><p role="alert">{error || "Game not found"}</p><button onClick={retry}>Retry</button> · <Link to="/schedule">Back to Schedule</Link></div>;
  const team = (abbr:string):Team => teams[abbr] ?? {abbr,name:abbr,city:"",record:""};
  const away = team(game.team1), home = team(game.team2);
  const live = game.status === "live";
  const status = game.status === "final" ? "Final" : live ? game.statusText || `Period ${game.period ?? "—"} · ${game.clock ?? ""}` : "Scheduled";
  const freshness = Object.entries(sourceStatus).filter(([name]) => /live|box/i.test(name)).map(([,status]) => status.last_success).filter((date):date is string => Boolean(date)).sort().at(-1);
  return <div className="px-5 sm:px-10 py-8 max-w-[1000px] mx-auto">
    <Link to="/schedule" className="text-muted">← Back to Schedule</Link>
    {error && <p role="alert" className="mt-3">Match refresh failed: {error} <button onClick={retry}>Retry</button></p>}
    {teamError && <p className="mt-3" role="alert">Team details unavailable <button onClick={retryTeams}>Retry</button></p>}
    <div className="bg-surface border border-line rounded-2xl p-5 sm:p-8 my-5">
      <p className="text-center text-muted">{game.date} · {formatGameTime(game)} · {game.venue || "Venue TBA"}</p>
      <p className="text-center font-bold my-3" aria-live="polite">{status}</p>
      {freshness && <p className="text-center text-xs text-muted">Source updated {new Date(freshness).toLocaleString()}</p>}
      <div className="flex items-center justify-between gap-3 my-6">
        {[away,home].map((t,index) => <div key={t.abbr} className="text-center flex-1 min-w-0">
          <TeamLogo team={t} abbr={t.abbr} size={56}/><h1 className="font-display font-bold text-xl mt-3">{t.city} {t.name}</h1>
          <p className="text-muted text-sm">{game.homeAbbr ? (game.homeAbbr === t.abbr ? "Home" : "Away") : "Home/away unavailable"}</p>
          {(index === 0 ? game.score1 : game.score2) !== null && <p className="text-4xl font-bold my-3">{index === 0 ? game.score1 : game.score2}</p>}
        </div>)}
      </div>
      {game.win1 !== null ? <><WinBar pct1={game.win1} team1={away} team2={home}/>{game.prediction && <p className="mt-4 text-sm text-muted">{game.prediction}</p>}</> : <p className="text-center text-muted">Prediction unavailable</p>}
    </div>
    <section className="bg-surface border border-line rounded-xl p-5 mb-5 overflow-auto">
      <h2 className="font-bold mb-3">Quarter scores</h2>
      {game.periodScores?.length ? <table className="w-full text-sm"><thead><tr><th className="text-left">Team</th>{game.periodScores.map(p => <th key={p.period}>{p.period <= 4 ? `Q${p.period}` : `OT${p.period - 4}`}</th>)}</tr></thead>
        <tbody>{[away,home].map((t,i) => <tr key={t.abbr}><th className="text-left py-2">{t.abbr}</th>{game.periodScores!.map(p => <td className="text-center" key={p.period}>{i === 0 ? p.score1 : p.score2}</td>)}</tr>)}</tbody></table> : <p className="text-muted">Quarter scores unavailable</p>}
    </section>
    <section className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
      {[away,home].map(t => <div key={t.abbr} className="bg-surface border border-line rounded-xl p-5">
        <h2 className="font-bold mb-3">{t.name} · Recent form</h2>
        {statsErrors[t.abbr] ? <p role="alert">{statsErrors[t.abbr]} <button className="underline" onClick={retryStats[t.abbr]}>Retry</button></p> : stats[t.abbr] ? <>
          <div className="flex gap-2 mb-4">{stats[t.abbr]!.form.map((result,i) => <FormBadge key={i} r={result}/>)}</div>
          <SparkLine color="var(--color-brand)" data={[...stats[t.abbr]!.lastScores].reverse()} width={260} height={64}/>
        </> : <p className="text-muted">Loading statistics…</p>}
      </div>)}
    </section>
    {game.status !== "scheduled" && <section className="bg-surface border border-line rounded-xl p-5">
      <h2 className="font-bold mb-3">Player box scores</h2>
      {boxLoading ? <p>Loading box scores…</p> : boxError ? <p role="alert">{boxError} <button onClick={retryBox}>Retry</button></p> : boxScore.length === 0 ? <p className="text-muted">Box scores not imported yet</p> : [away,home].map(t => <div key={t.abbr} className="overflow-auto mb-5">
        <h3 className="font-bold my-3">{t.name}</h3><table className="w-full text-sm text-left"><thead><tr>{["Player","MIN","PTS","REB","AST","STL","BLK"].map(h => <th key={h} className="p-2">{h}</th>)}</tr></thead>
          <tbody>{boxScore.filter(p => p.teamAbbr === t.abbr).map(p => <tr key={p.nbaId} className="border-t border-line"><td className="p-2">{p.name}</td>{[p.minutes.toFixed(1),p.points,p.rebounds,p.assists,p.steals,p.blocks].map((v,i) => <td key={i} className="p-2">{v}</td>)}</tr>)}</tbody></table>
      </div>)}
    </section>}
  </div>;
}
