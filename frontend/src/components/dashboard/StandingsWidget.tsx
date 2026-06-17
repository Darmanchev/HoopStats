import type { Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";

interface Props {
  teams: Record<string, Team>;
}

export default function StandingsWidget({ teams }: Props) {
  // Мок данные
  const standings = [
    { rank: 1, abbr: "DEN", gp: 34, w: 14, l: 3, pct: "0.824", l10: "L-10", strk: "W" },
    { rank: 2, abbr: "GSW", gp: 34, w: 13, l: 4, pct: "0.824", l10: "8-9", strk: "W" },
    { rank: 3, abbr: "LAC", gp: 33, w: 12, l: 5, pct: "0.870", l10: "5-8", strk: "L" },
    { rank: 4, abbr: "PHX", gp: 33, w: 12, l: 6, pct: "0.830", l10: "6-6", strk: "W" },
    { rank: 5, abbr: "LAL", gp: 33, w: 11, l: 5, pct: "0.834", l10: "4-6", strk: "W" },
  ];

  return (
    <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line h-full flex flex-col">
      <h2 className="font-display font-semibold text-[18px] text-ink mb-5">Standings (Western Conference)</h2>
      
      <div className="flex-1 overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-line text-[11px] font-bold text-ink uppercase tracking-wide">
              <th className="pb-3 px-2">Team</th>
              <th className="pb-3 px-2 text-center">GP</th>
              <th className="pb-3 px-2 text-center">W</th>
              <th className="pb-3 px-2 text-center">L</th>
              <th className="pb-3 px-2 text-center">PCT</th>
              <th className="pb-3 px-2 text-center">L10</th>
              <th className="pb-3 px-2 text-center">STRK</th>
            </tr>
          </thead>
          <tbody>
            {standings.map((row) => {
              const t = teams[row.abbr];
              return (
                <tr key={row.rank} className="border-b border-line/50 last:border-0 hover:bg-surface-2 transition-colors">
                  <td className="py-3 px-2">
                    <div className="flex items-center gap-3">
                      <span className="text-[13px] font-semibold text-ink w-3">{row.rank}</span>
                      {t && <TeamLogo team={t} abbr={t.abbr} size={24} />}
                      <span className="text-[14px] font-medium text-ink">{t ? t.name : row.abbr}</span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-center text-[13px] font-medium text-ink">{row.gp}</td>
                  <td className="py-3 px-2 text-center text-[13px] font-medium text-ink">{row.w}</td>
                  <td className="py-3 px-2 text-center text-[13px] font-medium text-ink">{row.l}</td>
                  <td className="py-3 px-2 text-center text-[13px] font-medium text-ink">{row.pct}</td>
                  <td className="py-3 px-2 text-center text-[13px] font-medium text-ink">{row.l10}</td>
                  <td className="py-3 px-2 text-center text-[13px] font-medium text-ink">{row.strk}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
