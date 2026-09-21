import type { LiveGame, PlayerGameStat, UpcomingGame } from "../../types";

interface Props {
  game?: LiveGame | UpcomingGame | null;
  players?: PlayerGameStat[];
}

export default function LiveGameStatsWidget({ game = null, players = [] }: Props) {
  const rows = [...players].sort((left, right) => right.points - left.points).slice(0, 6);

  return (
    <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line h-full flex flex-col">
      <div className="mb-4">
        <h2 className="font-display font-semibold text-[18px] text-ink leading-tight">Live Game Stats</h2>
        <p className="text-[13px] text-muted">{game ? `(${game.team1} vs ${game.team2})` : "Current leaders"}</p>
      </div>

      {!game || rows.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-faint text-sm">
          No live box score available
        </div>
      ) : (
      <div className="flex-1 overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-line text-[11px] font-bold text-ink uppercase tracking-wide">
              <th className="pb-2 px-2">Player</th>
              <th className="pb-2 px-2 text-center">Points</th>
              <th className="pb-2 px-2 text-center">Reb</th>
              <th className="pb-2 px-2 text-center">Ast</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((player) => (
              <tr key={player.nbaId} className="hover:bg-surface-2 transition-colors">
                <td className="py-2.5 px-2">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-surface-2 overflow-hidden border border-line shrink-0">
                      <img src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${player.nbaId}.png`} alt={player.name} className="w-full h-full object-cover" />
                    </div>
                    <div>
                      <div className="text-[13px] font-semibold text-ink leading-tight">{player.name}</div>
                      <div className="text-[10px] text-muted leading-tight">{player.teamAbbr}</div>
                    </div>
                  </div>
                </td>
                <td className="py-2.5 px-2 text-center text-[14px] font-semibold text-ink">{player.points}</td>
                <td className="py-2.5 px-2 text-center text-[14px] font-semibold text-ink">{player.rebounds}</td>
                <td className="py-2.5 px-2 text-center text-[14px] font-semibold text-ink">{player.assists}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      )}
    </div>
  );
}
