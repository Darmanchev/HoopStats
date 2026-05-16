import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import type { Team, TeamStats } from "../types";
import { getTeams, getTeamStats } from "../lib/api";
import TeamLogo from "../components/teams/TeamLogo";
import FormBadge from "../components/teams/FormBadge";
import SparkLine from "../components/teams/SparkLine";

export default function TeamDetail() {
  const { abbr } = useParams<{ abbr: string }>();
  const navigate = useNavigate();
  const [team, setTeam] = useState<Team | null>(null);
  const [stats, setStats] = useState<TeamStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!abbr) return;

    Promise.all([getTeams(), getTeamStats(abbr)])
      .then(([teamsMap, teamStats]) => {
        const found = teamsMap[abbr];
        if (!found) {
          setError("Team not found");
          return;
        }
        setTeam(found);
        setStats(teamStats);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [abbr]);

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

  if (error || !team) {
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
        <div style={{ fontSize: 16, color: "#C8102E" }}>{error || "Team not found"}</div>
        <button
          onClick={() => navigate("/teams")}
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
          Back to Teams
        </button>
      </div>
    );
  }

  const wins = parseInt(team.record.split("-")[0]) || 0;
  const losses = parseInt(team.record.split("-")[1]) || 0;
  const winPct = wins + losses > 0 ? (wins / (wins + losses) * 100).toFixed(1) : "0.0";

  return (
    <div style={{ padding: "36px 44px", maxWidth: 800, margin: "0 auto" }}>
      <button
        onClick={() => navigate("/teams")}
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
        Back to Teams
      </button>

      {/* Header */}
      <div
        style={{
          background: "#FFFFFF",
          border: "1px solid #1C2235",
          borderRadius: 16,
          padding: "32px 40px",
          marginBottom: 20,
          display: "flex",
          alignItems: "center",
          gap: 24,
        }}
      >
        <TeamLogo team={team} abbr={team.abbr} size={80} />
        <div>
          <div
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 800,
              fontSize: 32,
            }}
          >
            {team.city}{" "}
            <span style={{ color: team.accent }}>{team.name}</span>
          </div>
          <div style={{ fontSize: 16, color: "#6B7590", marginTop: 4 }}>
            {team.record} · {winPct}%
          </div>
        </div>
      </div>

      {/* Form */}
      {stats && stats.form.length > 0 ? (
        <div
          style={{
            background: "#FFFFFF",
            border: "1px solid #1C2235",
            borderRadius: 12,
            padding: "24px 28px",
            marginBottom: 20,
          }}
        >
          <div
            style={{
              fontSize: 11,
              letterSpacing: 1.2,
              color: "#8A94AE",
              fontWeight: 700,
              marginBottom: 12,
              textTransform: "uppercase",
            }}
          >
            Last 5 Games
          </div>
          <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
            {stats.form.map((r, i) => (
              <FormBadge key={i} r={r as "W" | "L"} />
            ))}
          </div>

          <div
            style={{
              fontSize: 11,
              letterSpacing: 1.2,
              color: "#8A94AE",
              fontWeight: 700,
              marginBottom: 12,
              textTransform: "uppercase",
            }}
          >
            Points — Last 10 Games
          </div>
          <SparkLine
            data={stats.lastScores}
            color={team.accent}
            width={600}
            height={80}
          />
        </div>
      ) : (
        <div
          style={{
            background: "#FFFFFF",
            border: "1px solid #1C2235",
            borderRadius: 12,
            padding: "24px 28px",
            textAlign: "center",
            color: "#8A94AE",
          }}
        >
          No stats available yet
        </div>
      )}
    </div>
  );
}
