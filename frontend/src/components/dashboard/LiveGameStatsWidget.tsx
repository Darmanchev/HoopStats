export default function LiveGameStatsWidget() {
  const players = [
    { name: "S. Gilgeous-Alexander", team: "OKC", pts: 32, reb: 9, ast: 9, img: "1628983" },
    { name: "J. Williams", team: "OKC", pts: 29, reb: 8, ast: 5, img: "1631114" },
    { name: "N. Jokic", team: "DEN", pts: 24, reb: 4, ast: 7, img: "203999" },
    { name: "J. Murray", team: "DEN", pts: 29, reb: 3, ast: 4, img: "1627750" },
    { name: "C. Holmgren", team: "OKC", pts: 19, reb: 4, ast: 3, img: "1631096" },
    { name: "A. Gordon", team: "DEN", pts: 17, reb: 3, ast: 0, img: "203932" },
  ];

  return (
    <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line h-full flex flex-col">
      <div className="mb-4">
        <h2 className="font-display font-semibold text-[18px] text-ink leading-tight">Live Game Stats</h2>
        <p className="text-[13px] text-muted">(OKC @ DEN)</p>
      </div>
      
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
            {players.map((p, i) => (
              <tr key={i} className="hover:bg-surface-2 transition-colors">
                <td className="py-2.5 px-2">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-surface-2 overflow-hidden border border-line shrink-0">
                      <img src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${p.img}.png`} alt={p.name} className="w-full h-full object-cover" />
                    </div>
                    <div>
                      <div className="text-[13px] font-semibold text-ink leading-tight">{p.name}</div>
                      <div className="text-[10px] text-muted leading-tight">{p.team}</div>
                    </div>
                  </div>
                </td>
                <td className="py-2.5 px-2 text-center text-[14px] font-semibold text-ink">{p.pts}</td>
                <td className="py-2.5 px-2 text-center text-[14px] font-semibold text-ink">{p.reb}</td>
                <td className="py-2.5 px-2 text-center text-[14px] font-semibold text-ink">{p.ast}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
