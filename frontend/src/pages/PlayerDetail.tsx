import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import type { PlayerDetail } from "../types";
import { getPlayer, getTeams } from "../lib/api";
import TeamLogo from "../components/teams/TeamLogo";

const statCategories = [
  { key: "pts", label: "Points", sub: "PPG", color: "#C8102E" },
  { key: "reb", label: "Rebounds", sub: "RPG", color: "#1E40AF" },
  { key: "ast", label: "Assists", sub: "APG", color: "#059669" },
  { key: "stl", label: "Steals", sub: "SPG", color: "#92400E" },
  { key: "blk", label: "Blocks", sub: "BPG", color: "#5B21B6" },
  { key: "mins", label: "Minutes", sub: "MPG", color: "#4A7FD4" },
];

const shootingStats = [
  { key: "fgPct", label: "FG%", color: "#C8102E" },
  { key: "fg3Pct", label: "3P%", color: "#1E40AF" },
  { key: "ftPct", label: "FT%", color: "#059669" },
];

export default function PlayerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [player, setPlayer] = useState<PlayerDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getPlayer(parseInt(id))
      .then(setPlayer)
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

  if (error || !player) {
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
        <div style={{ fontSize: 16, color: "#C8102E" }}>{error || "Player not found"}</div>
        <button
          onClick={() => navigate("/players")}
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
          Back to Players
        </button>
      </div>
    );
  }

  const teamFallback = {
    abbr: player.teamAbbr,
    name: player.teamName || "",
    city: player.teamCity || "",
    color: player.teamColor || "#1C2235",
    accent: player.teamAccent || "#4A7FD4",
    record: "0-0",
  };

  return (
    <div style={{ padding: "36px 44px", maxWidth: 800, margin: "0 auto" }}>
      <button
        onClick={() => navigate("/players")}
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
        Back to Players
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
        <TeamLogo team={teamFallback} abbr={player.teamAbbr} size={80} />
        <div>
          <div
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 800,
              fontSize: 32,
            }}
          >
            {player.name}
          </div>
          <div style={{ fontSize: 16, color: "#6B7590", marginTop: 4 }}>
            {player.position}
            {player.jerseyNumber ? ` · #${player.jerseyNumber}` : ""}
            <span style={{ marginLeft: 12 }}>
              {player.teamCity} {player.teamName}
            </span>
          </div>
          <div style={{ fontSize: 13, color: "#8A94AE", marginTop: 4 }}>
            {player.gamesPlayed} Games Played
          </div>
        </div>
      </div>

      {/* Per-game stats */}
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
            marginBottom: 16,
            textTransform: "uppercase",
          }}
        >
          Per Game Averages
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
          {statCategories.map(({ key, label, sub, color }) => (
            <div
              key={key}
              style={{
                textAlign: "center",
                padding: "16px 0",
                background: "#F8F9FD",
                borderRadius: 10,
              }}
            >
              <div
                style={{
                  fontFamily: "'Barlow Condensed',sans-serif",
                  fontWeight: 800,
                  fontSize: 28,
                  color,
                }}
              >
                {player[key as keyof PlayerDetail]?.toFixed?.(1) ?? "0.0"}
              </div>
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: 1,
                  color: "#8A94AE",
                  textTransform: "uppercase",
                  marginTop: 4,
                }}
              >
                {label}
              </div>
              <div style={{ fontSize: 11, color: "#BDC4D6" }}>{sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Shooting */}
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
            marginBottom: 16,
            textTransform: "uppercase",
          }}
        >
          Shooting
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
          {shootingStats.map(({ key, label, color }) => {
            const val = player[key as keyof PlayerDetail] as number;
            const pct = (val * 100).toFixed(1);
            return (
              <div
                key={key}
                style={{
                  textAlign: "center",
                  padding: "16px 0",
                  background: "#F8F9FD",
                  borderRadius: 10,
                }}
              >
                <div
                  style={{
                    fontFamily: "'Barlow Condensed',sans-serif",
                    fontWeight: 800,
                    fontSize: 28,
                    color,
                  }}
                >
                  {pct}%
                </div>
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: 1,
                    color: "#8A94AE",
                    textTransform: "uppercase",
                    marginTop: 4,
                  }}
                >
                  {label}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
