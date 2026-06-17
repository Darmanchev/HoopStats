export default function TeamEfficiencyChart() {
  return (
    <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line h-full flex flex-col relative overflow-hidden">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="font-display font-semibold text-[18px] text-ink leading-tight">Team Efficiency: Lakers</h2>
          <p className="text-[13px] text-muted">Points Per Game, Last 10 Games</p>
        </div>
        
        <button className="px-3 py-1.5 border border-line rounded-lg text-[12px] font-medium flex items-center gap-2 hover:bg-surface-2 transition-colors">
          Points
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
      </div>

      <div className="flex-1 w-full relative">
        <svg viewBox="0 0 400 150" className="w-full h-full overflow-visible" preserveAspectRatio="none">
          <defs>
            <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-brand)" stopOpacity="0.3" />
              <stop offset="100%" stopColor="var(--color-brand)" stopOpacity="0" />
            </linearGradient>
          </defs>
          
          <path 
            d="M 0 150 L 0 110 Q 30 50 60 70 T 120 90 T 180 60 T 240 50 T 300 90 T 360 40 L 400 40 L 400 150 Z" 
            fill="url(#chartGradient)" 
          />
          <path 
            d="M 0 110 Q 30 50 60 70 T 120 90 T 180 60 T 240 50 T 300 90 T 360 40 L 400 40" 
            fill="none" 
            stroke="var(--color-brand)" 
            strokeWidth="3" 
            strokeLinecap="round"
          />

          <g className="text-[10px] fill-ink font-semibold" transform="translate(0,-10)">
            <text x="0" y="100">105</text>
            <text x="60" y="60">118.5</text>
            <text x="120" y="80">112.5</text>
            <text x="180" y="50">118.0</text>
            <text x="240" y="40">118.5</text>
            <text x="300" y="80">113.0</text>
            <text x="360" y="30">118.5</text>
          </g>
        </svg>

        <div className="absolute right-0 top-1/2 -translate-y-1/2 flex flex-col items-end pr-2 pointer-events-none">
          <div className="text-[12px] font-bold text-muted uppercase tracking-wide">AVG</div>
          <div className="font-display font-extrabold text-[36px] text-ink leading-none my-1">118.5</div>
          <div className="text-[14px] font-semibold text-muted">PPG</div>
          <button className="mt-4 px-5 py-2 rounded-full border-2 border-brand text-brand font-semibold text-[12px] pointer-events-auto hover:bg-brand/5 transition-colors">
            View Data
          </button>
        </div>
      </div>
    </div>
  );
}
