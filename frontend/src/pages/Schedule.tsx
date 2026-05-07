import { useState } from "react";
import type { UpcomingGame, PastGame, Game, Team } from "../types";
import ScheduleRow from "../components/matches/ScheduleRow";

interface Props {
  upcoming: UpcomingGame[];
  past: PastGame[];
  teams: Record<string, Team>;
  onSelect: (game: UpcomingGame) => void;
}

type Filter = "all" | "upcoming" | "results";

export default function Schedule({ upcoming, past, teams, onSelect }: Props) {
  const [filter, setFilter] = useState<Filter>("all");

  const all: Game[] = [...past, ...upcoming].sort((a, b) =>
    a.dateRaw > b.dateRaw ? 1 : -1,
  );

  const filtered = all.filter((g) => {
    if (filter === "results") return "score1" in g;
    if (filter === "upcoming") return !("score1" in g);
    return true;
  });

  return (
    <div style={{ padding: "36px 44px", maxWidth: 860, margin: "0 auto" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          marginBottom: 28,
        }}
      >
        <div>
          <div
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 800,
              fontSize: 26,
              letterSpacing: 1.5,
              textTransform: "uppercase",
            }}
          >
            Schedule
          </div>
          <div style={{ fontSize: 13, color: "#6B7590", marginTop: 4 }}>
            2025–26 NBA Playoffs
          </div>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {(["all", "upcoming", "results"] as Filter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: "7px 16px",
                borderRadius: 7,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1,
                textTransform: "uppercase",
                cursor: "pointer",
                fontFamily: "'Barlow',sans-serif",
                background:
                  filter === f ? "oklch(0.55 0.18 25)" : "transparent",
                border: `1px solid ${filter === f ? "oklch(0.55 0.18 25)" : "#E4E8F2"}`,
                color: filter === f ? "#fff" : "#6B7590",
                transition: "all 0.15s",
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div
        style={{
          background: "#FFFFFF",
          border: "1px solid #1C2235",
          borderRadius: 14,
          overflow: "hidden",
        }}
      >
        {filtered.map((g, idx) => (
          <ScheduleRow
            key={g.id}
            game={g}
            team1={teams[g.team1]}
            team2={teams[g.team2]}
            isLast={idx === filtered.length - 1}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
