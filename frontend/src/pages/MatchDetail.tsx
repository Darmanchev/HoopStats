import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type { UpcomingGame, Team, TeamStats } from "../types";
import { getMatch, getTeamStats, getTeams } from "../lib/api";
import TeamLogo from "../components/teams/TeamLogo";
import WinBar from "../components/matches/WinBar";
import FormBadge from "../components/teams/FormBadge";
import SparkLine from "../components/teams/SparkLine";

export default function MatchDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [game, setGame] = useState<UpcomingGame | null>(null);
  const [teams, setTeams] = useState<Record<string, Team>>({});
  const [stats, setStats] = useState<Record<string, TeamStats>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    Promise.all([getMatch(id), getTeams()])
      .then(([gameData, teamsData]) => {
        setGame(gameData);
        setTeams(teamsData);
        return Promise.all([
          getTeamStats(gameData.team1),
          getTeamStats(gameData.team2),
        ]);
      })
      .then(([s1, s2]) => {
        if (game) {
          setStats({ [game.team1]: s1, [game.team2]: s2 });
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          fontFamily: "'Barlow Condensed',sans-serif",
          fontSize: 20,
          color: "#8A94AE",
          letterSpacing: 2,
        }}
      >
        LOADING...
      </div>
    );
  }

  if (error || !game) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          fontFamily: "'Barlow',sans-serif",
        }}
      >
        <div style={{ fontSize: 16, color: "#C8102E" }}>{error || "Game not found"}</div>
        <button
          onClick={() => navigate("/")}
          style={{
            marginTop: 24,
            padding: "10px 24px",
            background: "oklch(0.62 0.18 25)",
            color: "#fff",
            borderRadius: 8,
            border: "none",
            cursor: "pointer",
            fontWeight: 600,
          }}
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
    <div style={{ padding: "32px 44px", maxWidth: 880, margin: "0 auto" }}>
      <button
        onClick={() => navigate("/")}
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
        <WinBar pct1={win1} team1={t1} team2={t2} />
      </div>

      {game.prediction && (
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
            style={{
              fontSize: 14,
              color: "#4A6080",
              lineHeight: 1.7,
              margin: 0,
            }}
          >
            {game.prediction}
          </p>
        </div>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 14,
          marginBottom: 20,
        }}
      >
        {([game.team1, game.team2] as const).map((abbr) => {
          const t = teams[abbr];
          const s = stats[abbr];
          return (
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
              {s ? (
                <>
                  <div style={{ display: "flex", gap: 6, marginBottom: 18 }}>
                    {s.form.map((r, i) => (
                      <FormBadge key={i} r={r as "W" | "L"} />
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
                    data={s.lastScores}
                    color={t.accent}
                    width={210}
                    height={52}
                  />
                </>
              ) : (
                <div style={{ fontSize: 13, color: "#8A94AE" }}>
                  Loading...
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
