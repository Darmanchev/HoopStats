import type { Team, TeamStats } from "../../types";
import FormBadge from "./FormBadge";
import TeamLogo from "./TeamLogo";
import FavoriteButton from "../ui/FavoriteButton";

interface Props {team:Team;stats?:TeamStats;onClick:(abbr:string)=>void}
export default function TeamCard({team,stats,onClick}:Props) {
  const [wins,losses] = team.record.split("-").map(value=>parseInt(value) || 0);
  const winPct = wins+losses>0 ? (wins/(wins+losses)*100).toFixed(1) : "0.0";
  return <article className="bg-surface border border-line rounded-2xl shadow-[var(--shadow-card)] transition-all hover:border-line-strong hover:shadow-[var(--shadow-card-hover)]">
    <div role="button" aria-label={`Open team ${team.city} ${team.name}`} tabIndex={0}
      onClick={()=>onClick(team.abbr)} onKeyDown={event=>{if(event.key==="Enter" || event.key===" "){event.preventDefault();onClick(team.abbr);}}}
      className="px-6 pt-5 pb-4 cursor-pointer hover:bg-hover rounded-t-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40">
      <div className="flex items-center gap-3.5 mb-4"><TeamLogo team={team} abbr={team.abbr} size={48}/>
        <div><h2 className="font-display font-extrabold text-xl">{team.city} {team.name}</h2><p className="text-[13px] text-muted">{team.record} · {winPct}%</p></div>
      </div>
      {stats && stats.form.length>0 && <div><p className="text-[10px] font-bold text-faint mb-2">LAST 5</p><div className="flex gap-1">{stats.form.map((result,i)=><FormBadge key={i} r={result}/>)}</div></div>}
    </div>
    <div className="px-6 pb-5"><FavoriteButton team={team.abbr} name={`${team.city} ${team.name}`}/></div>
  </article>;
}
