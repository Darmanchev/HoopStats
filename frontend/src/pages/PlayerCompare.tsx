import { useCallback, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getPlayer, getPlayers } from "../lib/api";
import { useRemote } from "../hooks/useRemote";
import { usePlayerSeasons } from "../hooks/usePlayerSeasons";
import type { Player, PlayerDetail } from "../types";

function Picker({label,id,other,season,onSelect}:{label:string;id:number|null;other:number|null;season:string;onSelect:(id:number)=>void}) {
  const [query,setQuery] = useState("");
  const loader = useCallback(() => getPlayers({search:query,season,min_games:0,limit:10,sort_by:"name"}),[query,season]);
  const result = useRemote(season ? JSON.stringify([query,season]) : null,loader);
  return <div className="bg-surface border border-line rounded-xl p-4">
    <label className="block font-bold mb-2">{label}<input aria-label={`${label} search`} className="mt-2 block w-full p-2 border border-line bg-surface-2 rounded-lg font-normal" maxLength={100} value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search players…"/></label>
    {result.error ? <p role="alert">{result.error}</p> : <select className="w-full bg-surface p-2 border border-line rounded-lg" aria-label={label} value={id ?? ""} onChange={event=>onSelect(Number(event.target.value))}>
      <option value="" disabled>Choose player</option>
      {id && !result.data?.some(p=>p.id===id) && <option value={id}>Selected player #{id}</option>}
      {result.data?.filter(p=>p.id!==other).map((p:Player)=><option value={p.id} key={p.id}>{p.name} · {p.teamAbbr}</option>)}
    </select>}
  </div>;
}
const statistics:{key:keyof PlayerDetail;label:string;pct?:boolean}[] = [
  {key:"gamesPlayed",label:"Games played"},{key:"pts",label:"Points"},{key:"reb",label:"Rebounds"},{key:"ast",label:"Assists"},
  {key:"stl",label:"Steals"},{key:"blk",label:"Blocks"},{key:"mins",label:"Minutes"},
  {key:"fgPct",label:"FG%",pct:true},{key:"fg3Pct",label:"3P%",pct:true},{key:"ftPct",label:"FT%",pct:true},
];
export default function PlayerCompare() {
  const [params,setParams] = useSearchParams();
  const {seasons,loading,error} = usePlayerSeasons();
  const seasonParam = params.get("season");
  const season = seasonParam && seasons.includes(seasonParam) ? seasonParam : seasons[0] ?? "";
  const parseId = (value:string|null) => value && /^\d+$/.test(value) && Number(value)>0 ? Number(value) : null;
  const left = parseId(params.get("left")), rightValue = parseId(params.get("right"));
  const right = rightValue === left ? null : rightValue;
  const loadLeft = useCallback(()=>getPlayer(left!,season),[left,season]);
  const loadRight = useCallback(()=>getPlayer(right!,season),[right,season]);
  const a = useRemote(left && season ? `left:${left}:${season}` : null,loadLeft);
  const b = useRemote(right && season ? `right:${right}:${season}` : null,loadRight);
  function change(key:string,value:string){const next=new URLSearchParams(params);next.set(key,value);if(key!=="season")next.set("season",season);setParams(next);}
  return <div className="px-5 sm:px-10 py-8 max-w-[1000px] mx-auto">
    <Link to="/players" className="text-muted">← Back to Players</Link><h1 className="font-display font-bold text-2xl my-5">Compare players</h1>
    {loading ? <p>Loading seasons…</p> : error ? <p role="alert">{error}</p> : !seasons.length ? <p>No player seasons imported</p> : <>
      <label>Season <select aria-label="Season" value={season} className="bg-surface border border-line p-2 rounded-lg mb-5" onChange={e=>change("season",e.target.value)}>{seasons.map(s=><option key={s}>{s}</option>)}</select></label>
      <div className="grid sm:grid-cols-2 gap-4"><Picker label="First player" id={left} other={right} season={season} onSelect={id=>change("left",String(id))}/><Picker label="Second player" id={right} other={left} season={season} onSelect={id=>change("right",String(id))}/></div>
      {[a,b].map((result,i)=>result.error ? <p key={i} role="alert" className="mt-4">{result.error} <button onClick={result.retry}>Retry</button></p> : result.loading ? <p key={i}>Loading player…</p> : null)}
      {a.data && b.data ? <div className="overflow-auto bg-surface rounded-xl border border-line mt-5"><table className="w-full text-sm"><thead><tr><th className="p-3 text-left">Season averages · {season}</th><th>{a.data.name}</th><th>{b.data.name}</th></tr></thead><tbody>
        {statistics.map(stat=><tr key={stat.key} className="border-t border-line"><th className="text-left p-3">{stat.label}</th>{[a.data!,b.data!].map(p=>{const value=p[stat.key];return <td className="text-center p-3" key={p.id}>{typeof value === "number" ? stat.pct ? `${(value*100).toFixed(1)}%` : stat.key === "gamesPlayed" ? value : value.toFixed(1) : "Unavailable"}</td>;})}</tr>)}
      </tbody></table></div> : !a.error && !b.error && <p className="text-muted mt-5">Select two different players to compare their season averages.</p>}
    </>}
  </div>;
}
