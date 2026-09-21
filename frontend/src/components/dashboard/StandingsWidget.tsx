import { useState } from "react";

import type { Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";

interface Props {
  teams: Record<string, Team>;
}

type Conference = "East" | "West";

function recordParts(record: string) {
  const [wins = 0, losses = 0] = record.split("-").map(Number);
  const gamesPlayed = wins + losses;
  return {
    wins,
    losses,
    gamesPlayed,
    percentage: gamesPlayed ? wins / gamesPlayed : 0,
  };
}

export default function StandingsWidget({ teams }: Props) {
  const [conference, setConference] = useState<Conference>("East");
  const standings = Object.values(teams)
    .filter((team) => team.conference === conference)
    .map((team) => ({ team, ...recordParts(team.record) }))
    .sort((left, right) => {
      const leftRank = left.team.conferenceRank ?? Number.MAX_SAFE_INTEGER;
      const rightRank = right.team.conferenceRank ?? Number.MAX_SAFE_INTEGER;
      return leftRank - rightRank || right.percentage - left.percentage;
    })
    .slice(0, 8);

  return (
    <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line h-full flex flex-col">
      <div className="mb-5 flex items-center justify-between gap-3">
        <h2 className="font-display font-semibold text-[18px] text-ink">Standings</h2>
        <div className="flex rounded-full bg-surface-2 p-1" aria-label="Conference">
          {(["East", "West"] as const).map((name) => (
            <button
              key={name}
              type="button"
              aria-pressed={conference === name}
              onClick={() => setConference(name)}
              className={`rounded-full px-3 py-1 text-[12px] font-semibold transition-colors ${
                conference === name ? "bg-brand text-white" : "text-muted hover:text-ink"
              }`}
            >
              {name}
            </button>
          ))}
        </div>
      </div>

      {standings.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-faint text-sm">
          No {conference} standings available
        </div>
      ) : (
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
              {standings.map(({ team, gamesPlayed, wins, losses, percentage }, index) => (
                <tr key={team.abbr} className="border-b border-line/50 last:border-0 hover:bg-surface-2 transition-colors">
                  <td className="py-3 px-2">
                    <div className="flex items-center gap-3">
                      <span className="text-[13px] font-semibold text-ink w-3">{team.conferenceRank ?? index + 1}</span>
                      <TeamLogo team={team} abbr={team.abbr} size={24} />
                      <span className="text-[14px] font-medium text-ink">{team.name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-center text-[13px] font-medium text-ink">{gamesPlayed}</td>
                  <td className="py-3 px-2 text-center text-[13px] font-medium text-ink">{wins}</td>
                  <td className="py-3 px-2 text-center text-[13px] font-medium text-ink">{losses}</td>
                  <td className="py-3 px-2 text-center text-[13px] font-medium text-ink">{percentage.toFixed(3)}</td>
                  <td className="py-3 px-2 text-center text-[13px] font-medium text-ink">{team.lastTen ?? "—"}</td>
                  <td className="py-3 px-2 text-center text-[13px] font-medium text-ink">{team.streak ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
