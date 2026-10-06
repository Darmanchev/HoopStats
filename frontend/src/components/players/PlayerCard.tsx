import type { Player, Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";
import PlayerHeadshot from "./PlayerHeadshot";
import FavoriteButton from "../ui/FavoriteButton";

interface Props {
  player: Player;
  team?: Team;
  onClick: (id: number) => void;
}
const statItems = [
  {key:"pts" as const,label:"PPG",color:"#C8102E"},
  {key:"reb" as const,label:"RPG",color:"#1E40AF"},
  {key:"ast" as const,label:"APG",color:"#059669"},
];

export default function PlayerCard({player,team,onClick}:Props) {
  const t = team ?? {abbr:player.teamAbbr,name:"",city:"",record:""};
  return <article className="relative overflow-hidden bg-surface border border-line rounded-2xl shadow-[var(--shadow-card)] transition-all hover:border-line-strong hover:shadow-[var(--shadow-card-hover)]">
    <div role="button" aria-label={`Open player ${player.name}`} tabIndex={0}
      onClick={()=>onClick(player.id)} onKeyDown={event=>{if(event.key==="Enter" || event.key===" "){event.preventDefault();onClick(player.id);}}}
      className="flex cursor-pointer hover:bg-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40">
      <div className="flex-1 min-w-0 p-5">
        <div className="flex items-center gap-3 mb-4"><TeamLogo team={t} abbr={player.teamAbbr} size={38}/>
          <div className="min-w-0"><h2 className="font-display font-extrabold text-lg leading-tight truncate">{player.name}</h2>
            <p className="text-xs text-muted mt-1">{player.position}{player.jerseyNumber ? ` · #${player.jerseyNumber}` : ""} · {player.teamAbbr}</p>
          </div>
        </div>
        {statItems.map(stat=><div className="flex items-baseline gap-2" key={stat.key}><span className="font-display font-extrabold text-[22px] w-[52px] text-right" style={{color:stat.color}}>{player[stat.key].toFixed(1)}</span><span className="text-[10px] font-bold text-faint">{stat.label}</span></div>)}
        <p className="mt-3 text-[11px] text-faint font-semibold">{player.gamesPlayed} GP · {player.mins.toFixed(1)} MPG</p>
      </div>
      <PlayerHeadshot nbaId={player.nbaId} name={player.name} className="w-[108px] sm:w-[122px] shrink-0 pointer-events-none"/>
    </div>
    <div className="px-5 pb-4"><FavoriteButton player={player.id} name={player.name}/></div>
  </article>;
}
