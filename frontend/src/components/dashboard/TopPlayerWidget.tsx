import type { Player } from "../../types";

interface Props {
  player?: Player | null;
  onOpen?: (playerId: number) => void;
}

export default function TopPlayerWidget({ player = null, onOpen = () => undefined }: Props) {
  if (!player) {
    return (
      <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line h-full flex items-center justify-center">
        <span className="text-faint text-sm">No player leaders available</span>
      </div>
    );
  }

  return (
    <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line flex flex-col h-full">
      <h2 className="font-display font-semibold text-[18px] text-ink mb-6">Top Player Performance</h2>
      
      <div className="flex-1 flex flex-col justify-center">
        {/* Верхняя часть: фото и основные статы */}
        <div className="flex items-center justify-between mb-5">
          <div className="w-[80px] h-[80px] rounded-full bg-[#f2cc0c] overflow-hidden flex-shrink-0 relative border-[3px] border-surface shadow-sm">
            <img 
              src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${player.nbaId}.png`}
              alt={player.name}
              className="w-full h-full object-cover mt-2"
            />
          </div>
          
          <div className="flex items-center gap-6">
            <div className="text-center">
              <span className="font-display font-bold text-[34px] leading-none text-ink block">{player.pts}</span>
              <span className="text-[12px] font-bold text-ink tracking-wide mt-1 block">PTS</span>
            </div>
            <div className="text-center">
              <span className="font-display font-bold text-[34px] leading-none text-ink block">{player.reb}</span>
              <span className="text-[12px] font-bold text-ink tracking-wide mt-1 block">REB</span>
            </div>
            <div className="text-center">
              <span className="font-display font-bold text-[34px] leading-none text-ink block">{player.ast}</span>
              <span className="text-[12px] font-bold text-ink tracking-wide mt-1 block">AST</span>
            </div>
          </div>
        </div>

        {/* Нижняя часть: Имя и проценты */}
        <div className="flex items-start justify-between">
          <div>
            <div className="font-semibold text-[15px] text-ink leading-tight">{player.name}</div>
            <div className="text-[12px] text-muted mt-0.5">{player.teamAbbr}</div>
          </div>
          <div className="flex gap-6 text-center">
            <div className="flex flex-col items-center">
              <span className="text-[11px] text-muted font-medium mb-0.5">FG%</span>
              <span className="font-semibold text-[14px] text-ink">{player.fgPct}%</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-[11px] text-muted font-medium mb-0.5">MPG</span>
              <span className="font-semibold text-[14px] text-ink">{player.mins}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6">
        <button
          type="button"
          onClick={() => onOpen(player.id)}
          className="w-full py-2.5 rounded-full border border-[#1D4ED8] text-[#1D4ED8] font-semibold text-[14px] hover:bg-[#1D4ED8]/5 transition-colors"
        >
          View Profile
        </button>
      </div>
    </div>
  );
}
