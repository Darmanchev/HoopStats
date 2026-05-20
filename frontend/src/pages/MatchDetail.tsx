import { useParams, useNavigate } from "react-router-dom";
import TeamLogo from "../components/teams/TeamLogo";
import WinBar from "../components/matches/WinBar";
import FormBadge from "../components/teams/FormBadge";
import SparkLine from "../components/teams/SparkLine";
import { LoadingState } from "../components/ui/PageState";
import { useMatch } from "../hooks/useMatch";

export default function MatchDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { game, teams, stats, loading, error } = useMatch(id);

  if (loading) return <LoadingState />;

  if (error || !game) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4 px-6 text-center">
        <div className="text-sm text-brand">{error || "Game not found"}</div>
        <button
          onClick={() => navigate("/")}
          className="px-6 py-2.5 bg-brand text-white text-sm font-semibold rounded-lg
                     cursor-pointer border-none hover:opacity-90 transition-opacity"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  const t1 = teams[game.team1];
  const t2 = teams[game.team2];
  const win1 = game.win1 ?? 50;
  const fav = win1 >= 50 ? t1 : t2;
  const favPct = win1 >= 50 ? win1 : 100 - win1;

  if (!t1 || !t2) return null;

  return (
    <div className="px-6 sm:px-11 py-9 max-w-[880px] mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate("/")}
        className="flex items-center gap-1.5 text-[13px] text-muted cursor-pointer mb-7
                   bg-transparent border-none p-0 hover:text-ink transition-colors"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
          <path d="M19 12H5M12 5l-7 7 7 7" />
        </svg>
        Back to Dashboard
      </button>

      {/* Match hero card */}
      <div className="bg-surface border border-line rounded-2xl px-10 py-8 mb-5
                      shadow-[var(--shadow-card)]">
        <div className="text-center text-[11px] font-bold tracking-[1.5px] text-info uppercase mb-7">
          {game.date} · {game.time} · {game.venue}
        </div>

        <div className="flex items-center justify-between mb-7">
          {/* Team 1 */}
          <div className="text-center flex-1">
            <TeamLogo team={t1} abbr={game.team1} size={68} />
            <div className="font-display font-extrabold text-[26px] mt-3">{t1.city}</div>
            <div className="font-display font-bold text-[20px]" style={{ color: t1.accent }}>
              {t1.name}
            </div>
            <div className="text-[13px] text-muted mt-1">{t1.record}</div>
          </div>

          <div className="font-display font-black text-[52px] text-line-strong tracking-[6px]">
            VS
          </div>

          {/* Team 2 */}
          <div className="text-center flex-1">
            <TeamLogo team={t2} abbr={game.team2} size={68} />
            <div className="font-display font-extrabold text-[26px] mt-3">{t2.city}</div>
            <div className="font-display font-bold text-[20px]" style={{ color: t2.accent }}>
              {t2.name}
            </div>
            <div className="text-[13px] text-muted mt-1">{t2.record}</div>
          </div>
        </div>

        <WinBar pct1={win1} team1={t1} team2={t2} />
      </div>

      {/* Prediction */}
      {game.prediction && (
        <div className="bg-accent-bg border border-accent-fg/25
                        rounded-xl px-[26px] py-5 mb-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-1.5 h-1.5 rounded-full bg-accent-fg" />
            <span className="text-[11px] font-bold tracking-[1.5px] text-accent-fg uppercase">
              Prediction · {fav.name} favored at {favPct}%
            </span>
          </div>
          <p className="text-sm text-accent-fg/90 leading-relaxed m-0">
            {game.prediction}
          </p>
        </div>
      )}

      {/* Team stats side by side */}
      <div className="grid grid-cols-2 gap-3.5">
        {([game.team1, game.team2] as const).map((abbr) => {
          const t = teams[abbr];
          const s = stats[abbr];
          return (
            <div key={abbr} className="bg-surface border border-line rounded-xl px-[22px] py-5
                                       shadow-[var(--shadow-card)]">
              <div className="flex justify-between items-center mb-3.5">
                <span className="font-display font-bold text-[15px]" style={{ color: t.accent }}>
                  {t.city} {t.name}
                </span>
                <span className="text-[10px] tracking-[1.2px] text-faint font-bold uppercase">
                  LAST 5
                </span>
              </div>
              {s ? (
                <>
                  <div className="flex gap-1.5 mb-[18px]">
                    {s.form.map((r, i) => (
                      <FormBadge key={i} r={r as "W" | "L"} />
                    ))}
                  </div>
                  <div className="text-[10px] tracking-[1.2px] text-faint font-bold uppercase mb-2">
                    PTS — LAST 10 GAMES
                  </div>
                  <SparkLine data={s.lastScores} color={t.accent} width={210} height={52} />
                </>
              ) : (
                <div className="text-[13px] text-faint">Loading stats…</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
