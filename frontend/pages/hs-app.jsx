const { useState, useEffect, useRef } = React;
const D = window.HOOPDATA;

// ─── ATOMS ───────────────────────────────────────────────────

function TeamLogo({ abbr, size = 48 }) {
  const t = D.TEAMS[abbr];
  if (!t) return null;
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: t.color,
      border: `2px solid ${t.accent}33`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 800,
      fontSize: size * 0.32, color: t.accent, letterSpacing: '0.5px',
      flexShrink: 0
    }}>{abbr}</div>);

}

function FormBadge({ r }) {
  const win = r === 'W';
  return (
    <span style={{
      width: 26, height: 26, borderRadius: 5, display: 'inline-flex',
      alignItems: 'center', justifyContent: 'center',
      background: win ? 'oklch(0.88 0.08 145)' : 'oklch(0.90 0.06 15)',
      color: win ? 'oklch(0.28 0.14 145)' : 'oklch(0.32 0.12 15)',
      fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 800, fontSize: 13
    }}>{r}</span>);

}

function StatusPill({ status }) {
  const map = {
    'Out': ['oklch(0.92 0.06 12)', 'oklch(0.28 0.14 12)'],
    'Doubtful': ['oklch(0.92 0.06 40)', 'oklch(0.30 0.12 40)'],
    'Questionable': ['oklch(0.92 0.05 75)', 'oklch(0.28 0.12 75)'],
    'Day-to-Day': ['oklch(0.92 0.04 210)', 'oklch(0.26 0.10 210)']
  };
  const [bg, fg] = map[status] || map['Day-to-Day'];
  return (
    <span style={{
      padding: '3px 9px', borderRadius: 4, fontSize: 11, fontWeight: 600,
      background: bg, color: fg, whiteSpace: 'nowrap'
    }}>{status}</span>);

}

function Sparkline({ data, color, width = 180, height = 48 }) {
  if (!data || data.length < 2) return null;
  const max = Math.max(...data),min = Math.min(...data),rng = max - min || 1;
  const p = 6;
  const pts = data.map((v, i) => [
  p + i / (data.length - 1) * (width - p * 2),
  p + (1 - (v - min) / rng) * (height - p * 2)]
  );
  const d = pts.map((pt, i) => `${i ? 'L' : 'M'}${pt[0].toFixed(1)},${pt[1].toFixed(1)}`).join(' ');
  const fill = `${d} L${pts[pts.length - 1][0]},${height} L${pts[0][0]},${height} Z`;
  const last = pts[pts.length - 1];
  return (
    <svg width={width} height={height} style={{ overflow: 'visible', display: 'block' }}>
      <defs>
        <linearGradient id={`sg-${color.replace(/[^a-z0-9]/gi, '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={fill} fill={`url(#sg-${color.replace(/[^a-z0-9]/gi, '')})`} />
      <path d={d} fill="none" stroke={color} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={last[0]} cy={last[1]} r={3.5} fill={color} />
    </svg>);

}

function WinBar({ pct1, abbr1, abbr2 }) {
  const t1 = D.TEAMS[abbr1],t2 = D.TEAMS[abbr2];
  return (
    <div>
      <div style={{ display: 'flex', gap: 2, height: 5, borderRadius: 3, overflow: 'hidden', marginBottom: 8 }}>
        <div style={{ width: `${pct1}%`, background: t1.accent, transition: 'width 0.9s ease' }} />
        <div style={{ width: `${100 - pct1}%`, background: t2.accent, transition: 'width 0.9s ease' }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 700, fontSize: 14, color: t1.accent }}>{pct1}%</span>
        <span style={{ fontSize: 10, letterSpacing: 1.2, color: '#8A94AE', fontWeight: 700 }}>WIN PROBABILITY</span>
        <span style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 700, fontSize: 14, color: t2.accent }}>{100 - pct1}%</span>
      </div>
    </div>);

}

// ─── GAME CARD ────────────────────────────────────────────────

function GameCard({ game, onClick }) {
  const t1 = D.TEAMS[game.team1],t2 = D.TEAMS[game.team2];
  const [hov, setHov] = useState(false);
  return (
    <div
      onClick={() => onClick(game)}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        background: hov ? '#F2F4FF' : '#FFFFFF',
        border: `1px solid ${hov ? '#2C3450' : '#E4E8F2'}`,
        borderRadius: 14, padding: '22px 28px', cursor: 'pointer',
        transition: 'all 0.15s ease',
        transform: hov ? 'translateY(-2px)' : 'none',
        boxShadow: hov ? '0 8px 32px rgba(0,0,0,0.4)' : '0 2px 8px rgba(0,0,0,0.2)'
      }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.2, color: '#4A7FD4', textTransform: 'uppercase' }}>
          {game.date} · {game.time}
        </span>
        <span style={{ fontSize: 11, color: '#8A94AE' }}>{game.venue}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
        <TeamLogo abbr={game.team1} size={46} />
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 700, fontSize: 19, lineHeight: 1.1 }}>
            {t1.city} <span style={{ color: t1.accent }}>{t1.name}</span>
          </div>
          <div style={{ fontSize: 12, color: '#6B7590', marginTop: 3 }}>{t1.record}</div>
        </div>
        <span style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 800, fontSize: 16, color: '#C0CAD8', letterSpacing: 3 }}>VS</span>
        <div style={{ flex: 1, textAlign: 'right' }}>
          <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 700, fontSize: 19, lineHeight: 1.1 }}>
            <span style={{ color: t2.accent }}>{t2.name}</span> {t2.city}
          </div>
          <div style={{ fontSize: 12, color: '#6B7590', marginTop: 3 }}>{t2.record}</div>
        </div>
        <TeamLogo abbr={game.team2} size={46} />
      </div>

      <WinBar pct1={game.win1} abbr1={game.team1} abbr2={game.team2} />
    </div>);

}

// ─── FACTOR CARD ─────────────────────────────────────────────

function FactorCard({ f, t1, t2 }) {
  const edge = f.invert ?
  f.val1 < f.val2 ? 1 : f.val1 > f.val2 ? 2 : 0 :
  f.val1 > f.val2 ? 1 : f.val1 < f.val2 ? 2 : 0;
  return (
    <div style={{
      background: '#F8F9FC', border: '1px solid #181E2C',
      borderRadius: 10, padding: '16px 18px'
    }}>
      <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.4, color: '#8A94AE', textTransform: 'uppercase', marginBottom: 12 }}>
        {f.label}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 800, fontSize: 30,
            color: edge === 1 ? t1.accent : '#2A3248' }}>
            {f.val1}
          </div>
          {edge === 1 && <div style={{ fontSize: 10, fontWeight: 700, color: t1.accent, letterSpacing: 1 }}>▲ EDGE</div>}
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 800, fontSize: 30,
            color: edge === 2 ? t2.accent : '#2A3248' }}>
            {f.val2}
          </div>
          {edge === 2 && <div style={{ fontSize: 10, fontWeight: 700, color: t2.accent, letterSpacing: 1, textAlign: 'right' }}>▲ EDGE</div>}
        </div>
      </div>
    </div>);

}

// ─── VIEWS ───────────────────────────────────────────────────

function DashboardView({ onSelect }) {
  const today = D.UPCOMING.filter((g) => g.isToday);
  const coming = D.UPCOMING.filter((g) => !g.isToday);
  return (
    <div style={{ padding: '36px 44px', maxWidth: 860, margin: '0 auto' }}>
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 800, fontSize: 26, letterSpacing: 1.5, textTransform: 'uppercase' }}>
          Tonight's Games
        </div>
        <div style={{ fontSize: 13, color: '#6B7590', marginTop: 4 }}>April 25, 2026 · NBA Playoffs Round 1</div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginBottom: 44 }}>
        {today.map((g) => <GameCard key={g.id} game={g} onClick={onSelect} />)}
      </div>

      <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 700, fontSize: 14,
        letterSpacing: 1.6, color: '#8A94AE', textTransform: 'uppercase', marginBottom: 14 }}>
        Upcoming
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {coming.map((g) => <GameCard key={g.id} game={g} onClick={onSelect} />)}
      </div>
    </div>);

}

function MatchDetailView({ game, onBack }) {
  const t1 = D.TEAMS[game.team1],t2 = D.TEAMS[game.team2];
  const d1 = D.TEAM_DETAILS[game.team1],d2 = D.TEAM_DETAILS[game.team2];
  const fav = game.win1 >= 50 ? t1 : t2;
  const favPct = game.win1 >= 50 ? game.win1 : 100 - game.win1;

  return (
    <div style={{ padding: '32px 44px', maxWidth: 880, margin: '0 auto' }}>
      {/* back */}
      <button onClick={onBack} style={{
        background: 'none', border: 'none', color: '#6B7590', cursor: 'pointer',
        fontFamily: "'Barlow',sans-serif", fontSize: 13, display: 'flex',
        alignItems: 'center', gap: 6, marginBottom: 28, padding: 0
      }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M19 12H5M12 5l-7 7 7 7" /></svg>
        Back to Dashboard
      </button>

      {/* matchup header */}
      <div style={{ background: '#FFFFFF', border: '1px solid #1C2235', borderRadius: 16, padding: '32px 40px', marginBottom: 20 }}>
        <div style={{ textAlign: 'center', fontSize: 11, fontWeight: 700, letterSpacing: 1.5, color: '#4A7FD4', textTransform: 'uppercase', marginBottom: 28 }}>
          {game.date} · {game.time} · {game.venue}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
          <div style={{ textAlign: 'center', flex: 1 }}>
            <TeamLogo abbr={game.team1} size={68} />
            <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 800, fontSize: 26, marginTop: 12, letterSpacing: 1 }}>{t1.city}</div>
            <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 700, fontSize: 20, color: t1.accent }}>{t1.name}</div>
            <div style={{ fontSize: 13, color: '#6B7590', marginTop: 4 }}>{t1.record}</div>
          </div>

          <div style={{ textAlign: 'center', padding: '0 24px' }}>
            <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 900, fontSize: 52, color: '#EDF0F8', letterSpacing: 6 }}>VS</div>
          </div>

          <div style={{ textAlign: 'center', flex: 1 }}>
            <TeamLogo abbr={game.team2} size={68} />
            <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 800, fontSize: 26, marginTop: 12, letterSpacing: 1 }}>{t2.city}</div>
            <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 700, fontSize: 20, color: t2.accent }}>{t2.name}</div>
            <div style={{ fontSize: 13, color: '#6B7590', marginTop: 4 }}>{t2.record}</div>
          </div>
        </div>

        <WinBar pct1={game.win1} abbr1={game.team1} abbr2={game.team2} />
      </div>

      {/* prediction */}
      <div style={{
        background: 'oklch(0.94 0.015 225)', border: '1px solid oklch(0.20 0.05 225)',
        borderRadius: 12, padding: '20px 26px', marginBottom: 20
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'oklch(0.62 0.18 225)' }} />
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.5, color: 'oklch(0.62 0.18 225)', textTransform: 'uppercase' }}>
            Prediction · {fav.name} favored at {favPct}%
          </span>
        </div>
        <p style={{ fontSize: 14, color: '#4A6080', lineHeight: 1.7, margin: 0 }}>{game.prediction}</p>
      </div>

      {/* key factors */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.5, color: '#8A94AE', textTransform: 'uppercase', marginBottom: 14 }}>
          Key Factors
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
          {game.factors.map((f, i) => <FactorCard key={i} f={f} t1={t1} t2={t2} />)}
        </div>
      </div>

      {/* form + sparkline */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 20 }}>
        {[[game.team1, t1, d1], [game.team2, t2, d2]].map(([abbr, t, d]) =>
        <div key={abbr} style={{ background: '#FFFFFF', border: '1px solid #1C2235', borderRadius: 12, padding: '20px 22px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <span style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 700, fontSize: 15, color: t.accent }}>
                {t.city} {t.name}
              </span>
              <span style={{ fontSize: 10, letterSpacing: 1.2, color: '#8A94AE', fontWeight: 700 }}>LAST 5</span>
            </div>
            <div style={{ display: 'flex', gap: 6, marginBottom: 18 }}>
              {d.form.map((r, i) => <FormBadge key={i} r={r} />)}
            </div>
            <div style={{ fontSize: 10, letterSpacing: 1.2, color: '#8A94AE', fontWeight: 700, marginBottom: 8 }}>PTS — LAST 10 GAMES</div>
            <Sparkline data={d.lastScores} color={t.accent} width={210} height={52} />
          </div>
        )}
      </div>

      {/* injuries */}
      <div style={{ background: '#FFFFFF', border: '1px solid #1C2235', borderRadius: 12, padding: '20px 26px' }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.5, color: '#8A94AE', textTransform: 'uppercase', marginBottom: 18 }}>
          Injury Report
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          {[[game.team1, t1, d1], [game.team2, t2, d2]].map(([abbr, t, d]) =>
          <div key={abbr}>
              <div style={{ fontSize: 13, fontWeight: 600, color: t.accent, marginBottom: 12 }}>{t.city} {t.name}</div>
              {d.injuries.length === 0 ?
            <div style={{ fontSize: 13, color: '#8A94AE', fontStyle: 'italic' }}>No injuries reported</div> :
            d.injuries.map((inj, i) =>
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 12, marginBottom: 12, borderBottom: '1px solid #181E2C' }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 3 }}>{inj.name}</div>
                      <div style={{ fontSize: 11, color: '#6B7590' }}>{inj.pos} · {inj.injury}</div>
                    </div>
                    <StatusPill status={inj.status} />
                  </div>
            )
            }
            </div>
          )}
        </div>
      </div>
    </div>);

}

function ScheduleView({ onSelect }) {
  const [filter, setFilter] = useState('all');
  const all = [...D.PAST, ...D.UPCOMING].sort((a, b) => a.dateRaw > b.dateRaw ? 1 : -1);
  const filtered = all.filter((g) => {
    if (filter === 'results') return !!g.score1;
    if (filter === 'upcoming') return !g.score1;
    return true;
  });

  return (
    <div style={{ padding: '36px 44px', maxWidth: 860, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 28 }}>
        <div>
          <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 800, fontSize: 26, letterSpacing: 1.5, textTransform: 'uppercase' }}>Schedule</div>
          <div style={{ fontSize: 13, color: '#6B7590', marginTop: 4 }}>2025–26 NBA Playoffs</div>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {['all', 'upcoming', 'results'].map((f) =>
          <button key={f} onClick={() => setFilter(f)} style={{
            padding: '7px 16px', borderRadius: 7, fontSize: 11, fontWeight: 700,
            letterSpacing: 1, textTransform: 'uppercase', cursor: 'pointer',
            fontFamily: "'Barlow',sans-serif",
            background: filter === f ? 'oklch(0.55 0.18 25)' : 'transparent',
            border: `1px solid ${filter === f ? 'oklch(0.55 0.18 25)' : '#E4E8F2'}`,
            color: filter === f ? '#fff' : '#6B7590',
            transition: 'all 0.15s'
          }}>{f}</button>
          )}
        </div>
      </div>

      <div style={{ background: '#FFFFFF', border: '1px solid #1C2235', borderRadius: 14, overflow: 'hidden' }}>
        {filtered.map((g, idx) => {
          const t1 = D.TEAMS[g.team1],t2 = D.TEAMS[g.team2];
          const isPast = !!g.score1;
          return (
            <ScheduleRow key={g.id} g={g} t1={t1} t2={t2} isPast={isPast}
            isLast={idx === filtered.length - 1}
            onSelect={!isPast ? onSelect : null} />);

        })}
      </div>
    </div>);

}

function ScheduleRow({ g, t1, t2, isPast, isLast, onSelect }) {
  const [hov, setHov] = useState(false);
  return (
    <div
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      onClick={() => onSelect && onSelect(g)}
      style={{
        display: 'flex', alignItems: 'center', padding: '16px 24px',
        background: hov && !isPast ? '#EEF1FF' : 'transparent',
        borderBottom: isLast ? 'none' : '1px solid #181E2C',
        cursor: onSelect ? 'pointer' : 'default',
        transition: 'background 0.12s'
      }}>
      
      <div style={{ width: 80, fontSize: 12, color: '#6B7590', flexShrink: 0 }}>{g.date}</div>

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <TeamLogo abbr={g.team1} size={28} />
          <span style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 700, fontSize: 15 }}>
            {t1.city} <span style={{ color: t1.accent }}>{t1.name}</span>
          </span>
        </div>
        <span style={{ fontSize: 11, color: '#C8D0E0' }}>vs</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <TeamLogo abbr={g.team2} size={28} />
          <span style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 700, fontSize: 15 }}>
            {t2.city} <span style={{ color: t2.accent }}>{t2.name}</span>
          </span>
        </div>
      </div>

      {isPast ?
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
          <span style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 800, fontSize: 22,
          color: g.score1 > g.score2 ? t1.accent : '#8A909E' }}>{g.score1}</span>
          <span style={{ color: '#C8D0E0', fontSize: 14 }}>—</span>
          <span style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 800, fontSize: 22,
          color: g.score2 > g.score1 ? t2.accent : '#8A909E' }}>{g.score2}</span>
          <span style={{ padding: '3px 8px', background: '#F8F9FC', borderRadius: 4, fontSize: 10,
          fontWeight: 700, letterSpacing: 1, color: '#8A94AE', marginLeft: 4 }}>FINAL</span>
        </div> :

      <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexShrink: 0 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#4A7FD4' }}>{g.time}</span>
          <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
            <span style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 700, fontSize: 14, color: t1.accent }}>{g.win1}%</span>
            <span style={{ fontSize: 11, color: '#8A94AE' }}>·</span>
            <span style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 700, fontSize: 14, color: t2.accent }}>{100 - g.win1}%</span>
          </div>
          {onSelect && <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2E3650" strokeWidth="2" strokeLinecap="round"><path d="M5 12h14M12 5l7 7-7 7" /></svg>}
        </div>
      }
    </div>);

}

// ─── SIDEBAR ─────────────────────────────────────────────────

function Sidebar({ active, setView }) {
  const nav = [
  { id: 'dashboard', label: 'Dashboard',
    icon: 'M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z' },
  { id: 'schedule', label: 'Schedule',
    icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' }];

  const disabled = ['Teams', 'Players', 'Injuries', 'Analytics'];

  return (
    <div style={{
      width: 218, background: '#FAFBFF', borderRight: '1px solid #181E2C',
      display: 'flex', flexDirection: 'column', flexShrink: 0
    }}>
      {/* logo */}
      <div style={{ padding: '26px 22px', borderBottom: '1px solid #181E2C' }}>
        <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontWeight: 900, fontSize: 22, letterSpacing: 2.5, textTransform: 'uppercase' }}>
          Hoop<span style={{ color: 'oklch(0.62 0.18 25)' }}>Stats</span>
        </div>
        <div style={{ fontSize: 10, letterSpacing: 1.8, color: '#8A94AE', marginTop: 3 }}>NBA ANALYTICS</div>
      </div>

      {/* nav */}
      <nav style={{ padding: '14px 10px', flex: 1 }}>
        {nav.map((item) => {
          const isActive = active === item.id;
          return (
            <button key={item.id} onClick={() => setView(item.id)} style={{
              display: 'flex', alignItems: 'center', gap: 10, width: '100%',
              padding: '10px 12px', borderRadius: 8, marginBottom: 3,
              background: isActive ? 'oklch(0.90 0.04 220)' : 'transparent',
              border: `1px solid ${isActive ? 'oklch(0.75 0.06 220)' : 'transparent'}`,
              color: isActive ? '#1C2235' : '#6B7590',
              cursor: 'pointer', fontFamily: "'Barlow',sans-serif",
              fontWeight: 500, fontSize: 14, textAlign: 'left',
              transition: 'all 0.12s'
            }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d={item.icon} />
              </svg>
              {item.label}
            </button>);

        })}

        <div style={{ height: 1, background: '#EDF0F8', margin: '12px 4px' }} />

        {disabled.map((label) =>
        <div key={label} style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '10px 12px', borderRadius: 8, marginBottom: 3,
          color: '#BDC4D6'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 15, height: 15, background: '#EDF0F8', borderRadius: 3, flexShrink: 0 }} />
              <span style={{ fontFamily: "'Barlow',sans-serif", fontSize: 14 }}>{label}</span>
            </div>
            <span style={{ fontSize: 9, letterSpacing: 1.2, color: '#E4E8F2', fontWeight: 700 }}>SOON</span>
          </div>
        )}
      </nav>

      <div style={{ padding: '16px 22px', borderTop: '1px solid #181E2C' }}>
        <div style={{ fontSize: 10, letterSpacing: 1.4, color: '#BDC4D6', fontWeight: 700, marginBottom: 4 }}>2025–26 SEASON</div>
        <div style={{ fontSize: 12, color: '#8A94AE' }}>Playoffs · Round 1</div>
      </div>
    </div>);

}

// ─── APP ─────────────────────────────────────────────────────

function App() {
  const [view, setView] = useState('dashboard');
  const [game, setGame] = useState(null);

  function selectGame(g) {setGame(g);setView('detail');}
  function goBack() {setView('dashboard');setGame(null);}
  function navTo(v) {setView(v);setGame(null);}

  const sidebarActive = view === 'detail' ? 'dashboard' : view;

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: '#F4F6FC', color: '#1C2235' }}>
      <Sidebar active={sidebarActive} setView={navTo} />
      <main style={{ flex: 1, overflowY: 'auto', minWidth: 0, color: "rgb(189, 196, 216)" }}>
        {view === 'dashboard' && <DashboardView onSelect={selectGame} />}
        {view === 'schedule' && <ScheduleView onSelect={selectGame} />}
        {view === 'detail' && game && <MatchDetailView game={game} onBack={goBack} />}
      </main>
    </div>);

}

document.addEventListener('DOMContentLoaded', () => {
  ReactDOM.createRoot(document.getElementById('root')).render(<App />);
});