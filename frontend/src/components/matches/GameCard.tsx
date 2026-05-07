import { useState } from "react";
import type { UpcomingGame, Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";
import WinBar from "./WinBar";

interface Props {
  game: UpcomingGame;
  team1: Team;
  team2: Team;
  onClick: (game: UpcomingGame) => void;
}

export default function GameCard({ game, team1, team2, onClick }: Props) {
  const [hov, setHov] = useState(false);

  return (
    <div
      onClick={() => onClick(game)}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        background: hov ? "#F2F4FF" : "#FFFFFF",
        border: `1px solid ${hov ? "#2C3450" : "#E4E8F2"}`,
        borderRadius: 14,
        padding: "22px 28px",
        cursor: "pointer",
        transition: "all 0.15s ease",
        transform: hov ? "translateY(-2px)" : "none",
        boxShadow: hov
          ? "0 8px 32px rgba(0,0,0,0.4)"
          : "0 2px 8px rgba(0,0,0,0.2)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 18,
        }}
      >
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: 1.2,
            color: "#4A7FD4",
            textTransform: "uppercase",
          }}
        >
          {game.date} · {game.time}
        </span>
        <span style={{ fontSize: 11, color: "#8A94AE" }}>{game.venue}</span>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          marginBottom: 20,
        }}
      >
        <TeamLogo team={team1} abbr={game.team1} size={46} />
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 700,
              fontSize: 19,
              lineHeight: 1.1,
            }}
          >
            {team1.city}{" "}
            <span style={{ color: team1.accent }}>{team1.name}</span>
          </div>
          <div style={{ fontSize: 12, color: "#6B7590", marginTop: 3 }}>
            {team1.record}
          </div>
        </div>

        <span
          style={{
            fontFamily: "'Barlow Condensed',sans-serif",
            fontWeight: 800,
            fontSize: 16,
            color: "#C0CAD8",
            letterSpacing: 3,
          }}
        >
          VS
        </span>

        <div style={{ flex: 1, textAlign: "right" }}>
          <div
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 700,
              fontSize: 19,
              lineHeight: 1.1,
            }}
          >
            <span style={{ color: team2.accent }}>{team2.name}</span>{" "}
            {team2.city}
          </div>
          <div style={{ fontSize: 12, color: "#6B7590", marginTop: 3 }}>
            {team2.record}
          </div>
        </div>
        <TeamLogo team={team2} abbr={game.team2} size={46} />
      </div>

      <WinBar pct1={game.win1} team1={team1} team2={team2} />
    </div>
  );
}
