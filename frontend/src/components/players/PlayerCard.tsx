import { useState } from "react";
import type { Player, Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";

interface Props {
  player: Player;
  team?: Team;
  onClick: (id: number) => void;
}

const statItems = [
  { key: "pts" as const, label: "PPG", color: "#C8102E" },
  { key: "reb" as const, label: "RPG", color: "#1E40AF" },
  { key: "ast" as const, label: "APG", color: "#059669" },
];

export default function PlayerCard({ player, team, onClick }: Props) {
  const [hov, setHov] = useState(false);

  const fallbackTeam: Team = {
    abbr: player.teamAbbr,
    name: "",
    city: "",
    color: "#1C2235",
    accent: "#4A7FD4",
    record: "0-0",
  };

  const t = team || fallbackTeam;

  return (
    <div
      onClick={() => onClick(player.id)}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        background: hov ? "#F2F4FF" : "#FFFFFF",
        border: `1px solid ${hov ? "#2C3450" : "#E4E8F2"}`,
        borderRadius: 14,
        padding: "20px 24px",
        cursor: "pointer",
        transition: "all 0.15s ease",
        transform: hov ? "translateY(-2px)" : "none",
        boxShadow: hov
          ? "0 8px 32px rgba(0,0,0,0.4)"
          : "0 2px 8px rgba(0,0,0,0.2)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
        <TeamLogo team={t} abbr={player.teamAbbr} size={44} />
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 800,
              fontSize: 20,
            }}
          >
            {player.name}
          </div>
          <div style={{ fontSize: 13, color: "#6B7590", marginTop: 2 }}>
            {player.position}
            {player.jerseyNumber ? ` · #${player.jerseyNumber}` : ""}
            <span style={{ marginLeft: 8, color: "#8A94AE" }}>
              {player.teamAbbr}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 12 }}>
        {statItems.map(({ key, label, color }) => (
          <div
            key={key}
            style={{
              flex: 1,
              textAlign: "center",
              padding: "10px 0",
              background: "#F8F9FD",
              borderRadius: 8,
            }}
          >
            <div
              style={{
                fontFamily: "'Barlow Condensed',sans-serif",
                fontWeight: 800,
                fontSize: 22,
                color,
              }}
            >
              {player[key].toFixed(1)}
            </div>
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: 1,
                color: "#8A94AE",
                textTransform: "uppercase",
                marginTop: 2,
              }}
            >
              {label}
            </div>
          </div>
        ))}
      </div>

      <div
        style={{
          marginTop: 12,
          fontSize: 11,
          color: "#BDC4D6",
          textAlign: "right",
          fontWeight: 600,
        }}
      >
        {player.gamesPlayed} GP · {player.mins.toFixed(1)} MPG
      </div>
    </div>
  );
}
