import type { Team } from "../../types";

interface Props {
  pct1: number;
  team1: Team;
  team2: Team;
}

export default function WinBar({ pct1, team1, team2 }: Props) {
  return (
    <div>
      <div
        style={{
          display: "flex",
          gap: 2,
          height: 5,
          borderRadius: 3,
          overflow: "hidden",
          marginBottom: 8,
        }}
      >
        <div
          style={{
            width: `${pct1}%`,
            background: team1.accent,
            transition: "width 0.9s ease",
          }}
        />
        <div
          style={{
            width: `${100 - pct1}%`,
            background: team2.accent,
            transition: "width 0.9s ease",
          }}
        />
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span
          style={{
            fontFamily: "'Barlow Condensed',sans-serif",
            fontWeight: 700,
            fontSize: 14,
            color: team1.accent,
          }}
        >
          {pct1}%
        </span>
        <span
          style={{
            fontSize: 10,
            letterSpacing: 1.2,
            color: "#8A94AE",
            fontWeight: 700,
          }}
        >
          WIN PROBABILITY
        </span>
        <span
          style={{
            fontFamily: "'Barlow Condensed',sans-serif",
            fontWeight: 700,
            fontSize: 14,
            color: team2.accent,
          }}
        >
          {100 - pct1}%
        </span>
      </div>
    </div>
  );
}
