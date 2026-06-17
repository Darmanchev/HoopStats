import type { Team } from "../../types";
import { getTeamColors } from "../../utils/colors";

interface Props {
  pct1: number;
  team1: Team;
  team2: Team;
}

export default function WinBar({ pct1, team1, team2 }: Props) {
  return (
    <div>
      <div className="flex gap-0.5 h-[5px] rounded-[3px] overflow-hidden mb-2">
        {/* ширина и цвет приходят из данных — оставляем инлайн */}
        <div
          className="transition-[width] duration-[900ms] ease-out"
          style={{ width: `${pct1}%`, background: getTeamColors(team1.abbr).accent }}
        />
        <div
          className="transition-[width] duration-[900ms] ease-out"
          style={{ width: `${100 - pct1}%`, background: getTeamColors(team2.abbr).accent }}
        />
      </div>
      <div className="flex justify-between items-center">
        <span
          className="font-display font-bold text-sm"
          style={{ color: getTeamColors(team1.abbr).accent }}
        >
          {pct1.toFixed(1)}%
        </span>
        <span className="text-[10px] tracking-[1.2px] text-faint font-bold">
          WIN PROBABILITY
        </span>
        <span
          className="font-display font-bold text-sm"
          style={{ color: getTeamColors(team2.abbr).accent }}
        >
          {(100 - pct1).toFixed(1)}%
        </span>
      </div>
    </div>
  );
}
