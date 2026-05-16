import { useState } from "react";
import type { Game, UpcomingGame, Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";

interface Props {
  game: Game;
  team1: Team;
  team2: Team;
  isLast: boolean;
  onSelect?: (game: UpcomingGame) => void;
}

export default function ScheduleRow({
  game,
  team1,
  team2,
  isLast,
  onSelect,
}: Props) {
  const [hov, setHov] = useState(false);
  const isPast = "score1" in game; // отличаем прошедший от предстоящего

  return (
    <div
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      onClick={() => !isPast && onSelect && onSelect(game as UpcomingGame)}
      style={{
        display: "flex",
        alignItems: "center",
        padding: "16px 24px",
        background: hov && !isPast ? "#EEF1FF" : "transparent",
        borderBottom: isLast ? "none" : "1px solid #181E2C",
        cursor: !isPast && onSelect ? "pointer" : "default",
        transition: "background 0.12s",
      }}
    >
      <div style={{ width: 80, fontSize: 12, color: "#6B7590", flexShrink: 0 }}>
        {game.date}
      </div>

      {game.seasonType === "playoffs" && (
        <span
          style={{
            padding: "2px 6px",
            borderRadius: 4,
            fontSize: 9,
            fontWeight: 700,
            letterSpacing: 0.5,
            background: "#FEF3C7",
            color: "#92400E",
            textTransform: "uppercase",
            flexShrink: 0,
          }}
        >
          PO
        </span>
      )}

      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          gap: 10,
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <TeamLogo team={team1} abbr={game.team1} size={28} />
          <span
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 700,
              fontSize: 15,
            }}
          >
            {team1.city}{" "}
            <span style={{ color: team1.accent }}>{team1.name}</span>
          </span>
        </div>
        <span style={{ fontSize: 11, color: "#C8D0E0" }}>vs</span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <TeamLogo team={team2} abbr={game.team2} size={28} />
          <span
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 700,
              fontSize: 15,
            }}
          >
            {team2.city}{" "}
            <span style={{ color: team2.accent }}>{team2.name}</span>
          </span>
        </div>
      </div>

      {isPast ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            flexShrink: 0,
          }}
        >
          <span
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 800,
              fontSize: 22,
              color: game.score1 > game.score2 ? team1.accent : "#8A909E",
            }}
          >
            {game.score1}
          </span>
          <span style={{ color: "#C8D0E0", fontSize: 14 }}>—</span>
          <span
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 800,
              fontSize: 22,
              color: game.score2 > game.score1 ? team2.accent : "#8A909E",
            }}
          >
            {game.score2}
          </span>
          <span
            style={{
              padding: "3px 8px",
              background: "#F8F9FC",
              borderRadius: 4,
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: 1,
              color: "#8A94AE",
              marginLeft: 4,
            }}
          >
            FINAL
          </span>
        </div>
      ) : (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: 13, fontWeight: 600, color: "#4A7FD4" }}>
            {game.time}
          </span>
          <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
            <span
              style={{
                fontFamily: "'Barlow Condensed',sans-serif",
                fontWeight: 700,
                fontSize: 14,
                color: team1.accent,
              }}
            >
              {game.win1}%
            </span>
            <span style={{ fontSize: 11, color: "#8A94AE" }}>·</span>
            <span
              style={{
                fontFamily: "'Barlow Condensed',sans-serif",
                fontWeight: 700,
                fontSize: 14,
                color: team2.accent,
              }}
            >
              {100 - game.win1}%
            </span>
          </div>
          {onSelect && (
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#2E3650"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          )}
        </div>
      )}
    </div>
  );
}
