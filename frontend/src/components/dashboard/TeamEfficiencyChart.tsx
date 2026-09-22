import type { Team } from "../../types";
import { getTeamColors } from "../../utils/colors";
import SparkLine from "../teams/SparkLine";

interface Props {
  teams?: Record<string, Team>;
  selectedAbbr?: string | null;
  onSelect?: (teamAbbr: string) => void;
  onOpen?: (teamAbbr: string) => void;
}

export default function TeamEfficiencyChart({
  teams = {},
  selectedAbbr = null,
  onSelect = () => undefined,
  onOpen = () => undefined,
}: Props) {
  const choices = Object.values(teams)
    .filter((team) => (team.stats?.lastScores.length ?? 0) > 0)
    .sort((left, right) => left.name.localeCompare(right.name));
  const selected = (selectedAbbr && teams[selectedAbbr]) || choices[0] || null;
  const scores = selected?.stats?.lastScores ?? [];
  const average = scores.length
    ? scores.reduce((sum, score) => sum + score, 0) / scores.length
    : null;

  return (
    <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line h-full flex flex-col relative overflow-hidden">
      <div className="flex justify-between items-start gap-4 mb-6">
        <div>
          <h2 className="font-display font-semibold text-[18px] text-ink leading-tight">
            Team Efficiency{selected ? `: ${selected.name}` : ""}
          </h2>
          <p className="text-[13px] text-muted">Points Per Game, Last 10 Games</p>
        </div>

        <select
          aria-label="Team"
          value={selected?.abbr ?? ""}
          onChange={(event) => onSelect(event.target.value)}
          className="px-3 py-1.5 border border-line rounded-lg text-[12px] font-medium bg-surface text-ink"
        >
          {choices.length === 0 && <option value="">No teams</option>}
          {choices.map((team) => (
            <option key={team.abbr} value={team.abbr}>{team.abbr}</option>
          ))}
        </select>
      </div>

      {selected && scores.length > 0 && average !== null ? (
        <div className="flex-1 flex items-center justify-between gap-6 min-h-[150px]">
          <div className="min-w-0 overflow-x-auto">
            <SparkLine
              data={[...scores].reverse()}
              color={getTeamColors(selected.abbr).accent}
              width={400}
              height={120}
              showValues
            />
          </div>
          <div className="shrink-0 text-right">
            <div className="text-[12px] font-bold text-muted uppercase tracking-wide">AVG</div>
            <div className="font-display font-extrabold text-[36px] text-ink leading-none my-1">
              {average.toFixed(1)}
            </div>
            <div className="text-[14px] font-semibold text-muted">PPG</div>
            <button
              type="button"
              onClick={() => onOpen(selected.abbr)}
              className="mt-4 rounded-full border-2 border-brand px-5 py-2 text-[12px] font-semibold text-brand transition-colors hover:bg-brand/5"
            >
              View Data
            </button>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-faint text-sm">
          No team scoring history available
        </div>
      )}
    </div>
  );
}
