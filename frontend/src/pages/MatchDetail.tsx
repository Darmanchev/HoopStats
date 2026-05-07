import type { UpcomingGame, Team, TeamDetails } from "../types";
import TeamLogo from "../components/teams/TeamLogo";
import WinBar from "../components/matches/WinBar";
import FactorCard from "../components/predictions/FactorCard";
import FormBadge from "../components/teams/FormBadge";
import SparkLine from "../components/teams/SparkLine";
import StatusPill from "../components/ui/StatusPill";

interface Props {
  game: UpcomingGame;
  teams: Record<string, Team>;
  teamDetails: Record<string, TeamDetails>;
  onBack: () => void;
}

export default function MatchDetail({
  game,
  teams,
  teamDetails,
  onBack,
}: Props) {
  const t1 = teams[game.team1];
  const t2 = teams[game.team2];
  const d1 = teamDetails[game.team1];
  const d2 = teamDetails[game.team2];
  const fav = game.win1 >= 50 ? t1 : t2;
  const favPct = game.win1 >= 50 ? game.win1 : 100 - game.win1;

  return (
    <div style={{ padding: "32px 44px", maxWidth: 880, margin: "0 auto" }}>
      <button
        onClick={onBack}
        style={{
          background: "none",
          border: "none",
          color: "#6B7590",
          cursor: "pointer",
          fontFamily: "'Barlow',sans-serif",
          fontSize: 13,
          display: "flex",
          alignItems: "center",
          gap: 6,
          marginBottom: 28,
          padding: 0,
        }}
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
        >
          <path d="M19 12H5M12 5l-7 7 7 7" />
        </svg>
        Back to Dashboard
      </button>

      {/* Шапка матча */}
      <div
        style={{
          background: "#FFFFFF",
          border: "1px solid #1C2235",
          borderRadius: 16,
          padding: "32px 40px",
          marginBottom: 20,
        }}
      >
        <div
          style={{
            textAlign: "center",
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: 1.5,
            color: "#4A7FD4",
            textTransform: "uppercase",
            marginBottom: 28,
          }}
        >
          {game.date} · {game.time} · {game.venue}
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 28,
          }}
        >
          <div style={{ textAlign: "center", flex: 1 }}>
            <TeamLogo team={t1} abbr={game.team1} size={68} />
            <div
              style={{
                fontFamily: "'Barlow Condensed',sans-serif",
                fontWeight: 800,
                fontSize: 26,
                marginTop: 12,
              }}
            >
              {t1.city}
            </div>
            <div
              style={{
                fontFamily: "'Barlow Condensed',sans-serif",
                fontWeight: 700,
                fontSize: 20,
                color: t1.accent,
              }}
            >
              {t1.name}
            </div>
            <div style={{ fontSize: 13, color: "#6B7590", marginTop: 4 }}>
              {t1.record}
            </div>
          </div>
          <div
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 900,
              fontSize: 52,
              color: "#EDF0F8",
              letterSpacing: 6,
            }}
          >
            VS
          </div>
          <div style={{ textAlign: "center", flex: 1 }}>
            <TeamLogo team={t2} abbr={game.team2} size={68} />
            <div
              style={{
                fontFamily: "'Barlow Condensed',sans-serif",
                fontWeight: 800,
                fontSize: 26,
                marginTop: 12,
              }}
            >
              {t2.city}
            </div>
            <div
              style={{
                fontFamily: "'Barlow Condensed',sans-serif",
                fontWeight: 700,
                fontSize: 20,
                color: t2.accent,
              }}
            >
              {t2.name}
            </div>
            <div style={{ fontSize: 13, color: "#6B7590", marginTop: 4 }}>
              {t2.record}
            </div>
          </div>
        </div>
        <WinBar pct1={game.win1} team1={t1} team2={t2} />
      </div>

      {/* Прогноз */}
      <div
        style={{
          background: "oklch(0.94 0.015 225)",
          border: "1px solid oklch(0.20 0.05 225)",
          borderRadius: 12,
          padding: "20px 26px",
          marginBottom: 20,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginBottom: 12,
          }}
        >
          <div
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: "oklch(0.62 0.18 225)",
            }}
          />
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: 1.5,
              color: "oklch(0.62 0.18 225)",
              textTransform: "uppercase",
            }}
          >
            Prediction · {fav.name} favored at {favPct}%
          </span>
        </div>
        <p
          style={{ fontSize: 14, color: "#4A6080", lineHeight: 1.7, margin: 0 }}
        >
          {game.prediction}
        </p>
      </div>

      {/* Ключевые факторы */}
      <div style={{ marginBottom: 20 }}>
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: 1.5,
            color: "#8A94AE",
            textTransform: "uppercase",
            marginBottom: 14,
          }}
        >
          Key Factors
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: 10,
          }}
        >
          {game.factors.map((f, i) => (
            <FactorCard key={i} factor={f} team1={t1} team2={t2} />
          ))}
        </div>
      </div>

      {/* Форма и спарклайн */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 14,
          marginBottom: 20,
        }}
      >
        {(
          [
            [game.team1, t1, d1],
            [game.team2, t2, d2],
          ] as const
        ).map(([abbr, t, d]) => (
          <div
            key={abbr}
            style={{
              background: "#FFFFFF",
              border: "1px solid #1C2235",
              borderRadius: 12,
              padding: "20px 22px",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 14,
              }}
            >
              <span
                style={{
                  fontFamily: "'Barlow Condensed',sans-serif",
                  fontWeight: 700,
                  fontSize: 15,
                  color: t.accent,
                }}
              >
                {t.city} {t.name}
              </span>
              <span
                style={{
                  fontSize: 10,
                  letterSpacing: 1.2,
                  color: "#8A94AE",
                  fontWeight: 700,
                }}
              >
                LAST 5
              </span>
            </div>
            <div style={{ display: "flex", gap: 6, marginBottom: 18 }}>
              {d.form.map((r, i) => (
                <FormBadge key={i} r={r} />
              ))}
            </div>
            <div
              style={{
                fontSize: 10,
                letterSpacing: 1.2,
                color: "#8A94AE",
                fontWeight: 700,
                marginBottom: 8,
              }}
            >
              PTS — LAST 10 GAMES
            </div>
            <SparkLine
              data={d.lastScores}
              color={t.accent}
              width={210}
              height={52}
            />
          </div>
        ))}
      </div>

      {/* Травмы */}
      <div
        style={{
          background: "#FFFFFF",
          border: "1px solid #1C2235",
          borderRadius: 12,
          padding: "20px 26px",
        }}
      >
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: 1.5,
            color: "#8A94AE",
            textTransform: "uppercase",
            marginBottom: 18,
          }}
        >
          Injury Report
        </div>
        <div
          style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}
        >
          {(
            [
              [game.team1, t1, d1],
              [game.team2, t2, d2],
            ] as const
          ).map(([abbr, t, d]) => (
            <div key={abbr}>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: t.accent,
                  marginBottom: 12,
                }}
              >
                {t.city} {t.name}
              </div>
              {d.injuries.length === 0 ? (
                <div
                  style={{
                    fontSize: 13,
                    color: "#8A94AE",
                    fontStyle: "italic",
                  }}
                >
                  No injuries reported
                </div>
              ) : (
                d.injuries.map((inj, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      paddingBottom: 12,
                      marginBottom: 12,
                      borderBottom: "1px solid #181E2C",
                    }}
                  >
                    <div>
                      <div
                        style={{
                          fontSize: 13,
                          fontWeight: 600,
                          marginBottom: 3,
                        }}
                      >
                        {inj.name}
                      </div>
                      <div style={{ fontSize: 11, color: "#6B7590" }}>
                        {inj.pos} · {inj.injury}
                      </div>
                    </div>
                    <StatusPill status={inj.status} />
                  </div>
                ))
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
