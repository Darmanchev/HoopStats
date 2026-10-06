import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { getPlayerGames } from "../../lib/api";
import { useRemote } from "../../hooks/useRemote";
import SparkLine from "../teams/SparkLine";
export default function PlayerGameLog({id,season}:{id:number;season?:string}) {
  const [page,setPage] = useState(0);
  const loader = useCallback(()=>getPlayerGames(id,season,page*20),[id,season,page]);
  const result = useRemote(`${id}:${season}:${page}`,loader);
  return <section className="bg-surface border border-line rounded-xl p-5 mt-5">
    <h2 className="font-bold text-lg mb-3">Game log</h2>
    {result.loading ? <p>Loading game log…</p> : result.error ? <p role="alert">{result.error} <button onClick={result.retry}>Retry</button></p> : result.data && <>
      <p className="text-sm text-muted mb-4">{result.data.coverage.note}</p>
      {!result.data.coverage.identityResolved ? <p>Official player identity unavailable</p> : !result.data.items.length ? <p>No game logs imported for this player and season</p> : <>
        <p className="text-sm text-muted">Points trend · this page, oldest to newest</p>
        <SparkLine data={[...result.data.items].reverse().map(g=>g.points)} color="var(--color-brand)" width={320} height={80} showValues/>
        <div className="overflow-auto"><table className="w-full text-left text-sm"><thead><tr>{["Date","Opponent","Result","MIN","PTS","REB","AST","STL","BLK"].map(h=><th key={h} className="p-2">{h}</th>)}</tr></thead><tbody>{result.data.items.map(g=><tr key={g.gameId} className="border-t border-line"><td className="p-2 whitespace-nowrap"><Link className="underline" to={`/match/${encodeURIComponent(g.gameId)}`}>{g.date}</Link></td><td>{g.homeAway === "Home" ? "vs" : g.homeAway === "Away" ? "at" : "vs (home/away unknown)"} {g.opponent}</td><td>{g.result ?? "—"}</td>{[g.minutes.toFixed(1),g.points,g.rebounds,g.assists,g.steals,g.blocks].map((value,i)=><td key={i}>{value}</td>)}</tr>)}</tbody></table></div>
      </>}
      <div className="flex gap-3 mt-4"><button disabled={page===0} onClick={()=>setPage(p=>p-1)}>Previous</button><span>Page {page+1} · {result.data.total} imported games</span><button disabled={(page+1)*20>=result.data.total} onClick={()=>setPage(p=>p+1)}>Next</button></div>
    </>}
  </section>;
}
