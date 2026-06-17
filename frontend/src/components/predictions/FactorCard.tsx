import type { Factor, Team } from "../../types";
import { getTeamColors } from "../../utils/colors";

interface Props {
  factor: Factor;
  team1: Team;
  team2: Team;
}

export default function FactorCard({ factor, team1, team2 }: Props) {
  const edge = factor.invert
    ? factor.val1 < factor.val2
      ? 1
      : factor.val1 > factor.val2
        ? 2
        : 0
    : factor.val1 > factor.val2
      ? 1
      : factor.val1 < factor.val2
        ? 2
        : 0;
  return (
    <div className="bg-surface-2 border border-line rounded-xl px-[18px] py-4">
      <div className="text-[10px] font-bold tracking-[1.4px] text-faint uppercase mb-3">
        {factor.label}
      </div>
      <div className="flex justify-between items-end">
        <div>
          <div
            className="font-display font-extrabold text-[30px]"
            style={{ color: edge === 1 ? getTeamColors(team1.abbr).accent : "var(--color-ink)" }}
          >
            {factor.val1}
          </div>
          {edge === 1 && (
            <div
              className="text-[10px] font-bold tracking-wide"
              style={{ color: getTeamColors(team1.abbr).accent }}
            >
              ▲ EDGE
            </div>
          )}
        </div>
        <div className="text-right">
          <div
            className="font-display font-extrabold text-[30px]"
            style={{ color: edge === 2 ? getTeamColors(team2.abbr).accent : "var(--color-ink)" }}
          >
            {factor.val2}
          </div>
          {edge === 2 && (
            <div
              className="text-[10px] font-bold tracking-wide text-right"
              style={{ color: getTeamColors(team2.abbr).accent }}
            >
              ▲ EDGE
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
