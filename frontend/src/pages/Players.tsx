import { useNavigate } from "react-router-dom";
import { usePlayers } from "../hooks/usePlayers";
import { useTeams } from "../hooks/useTeams";
import PlayerCard from "../components/players/PlayerCard";
import { useState } from "react";

type SortBy = "pts" | "reb" | "ast" | "games_played" | "name";
type PositionFilter = "all" | "G" | "F" | "C";

export default function Players() {
  const navigate = useNavigate();
  const { teams, loading: teamsLoading } = useTeams();
  const [sortBy, setSortBy] = useState<SortBy>("pts");
  const [positionFilter, setPositionFilter] = useState<PositionFilter>("all");
  const [search, setSearch] = useState("");
  const [minGames] = useState(10);

  const { players, loading, error } = usePlayers({
    sortBy,
    position: positionFilter === "all" ? undefined : positionFilter,
    minGames,
    limit: 200,
  });

  const filtered = players.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.teamAbbr.toLowerCase().includes(search.toLowerCase())
  );

  if (loading || teamsLoading) {
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

  if (error) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          fontFamily: "'Barlow',sans-serif",
          fontSize: 16,
          color: "#C8102E",
        }}
      >
        {error}
      </div>
    );
  }

  const sortOptions: { key: SortBy; label: string }[] = [
    { key: "pts", label: "PPG" },
    { key: "reb", label: "RPG" },
    { key: "ast", label: "APG" },
    { key: "games_played", label: "GP" },
    { key: "name", label: "Name" },
  ];

  return (
    <div style={{ padding: "36px 44px", maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ marginBottom: 28 }}>
        <div
          style={{
            fontFamily: "'Barlow Condensed',sans-serif",
            fontWeight: 800,
            fontSize: 26,
            letterSpacing: 1.5,
            textTransform: "uppercase",
          }}
        >
          Players
        </div>
        <div style={{ fontSize: 13, color: "#6B7590", marginTop: 4 }}>
          {filtered.length} players · {minGames}+ GP
        </div>
      </div>

      <div
        style={{
          display: "flex",
          gap: 12,
          marginBottom: 24,
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <input
          type="text"
          placeholder="Search players..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            padding: "8px 14px",
            borderRadius: 8,
            border: "1px solid #E4E8F2",
            fontSize: 14,
            fontFamily: "'Barlow',sans-serif",
            outline: "none",
            width: 240,
          }}
        />

        <div style={{ display: "flex", gap: 6 }}>
          {sortOptions.map((s) => (
            <button
              key={s.key}
              onClick={() => setSortBy(s.key)}
              style={{
                padding: "7px 14px",
                borderRadius: 7,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1,
                textTransform: "uppercase",
                cursor: "pointer",
                fontFamily: "'Barlow',sans-serif",
                background: sortBy === s.key ? "oklch(0.55 0.18 25)" : "transparent",
                border: `1px solid ${sortBy === s.key ? "oklch(0.55 0.18 25)" : "#E4E8F2"}`,
                color: sortBy === s.key ? "#fff" : "#6B7590",
              }}
            >
              {s.label}
            </button>
          ))}
        </div>

        <div style={{ display: "flex", gap: 6 }}>
          {(["all", "G", "F", "C"] as PositionFilter[]).map((p) => (
            <button
              key={p}
              onClick={() => setPositionFilter(p)}
              style={{
                padding: "7px 14px",
                borderRadius: 7,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1,
                cursor: "pointer",
                fontFamily: "'Barlow',sans-serif",
                background: positionFilter === p ? "oklch(0.45 0.15 220)" : "transparent",
                border: `1px solid ${positionFilter === p ? "oklch(0.45 0.15 220)" : "#E4E8F2"}`,
                color: positionFilter === p ? "#fff" : "#6B7590",
              }}
            >
              {p === "all" ? "All" : p === "G" ? "Guards" : p === "F" ? "Forwards" : "Centers"}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "48px 0",
            color: "#8A94AE",
            fontFamily: "'Barlow',sans-serif",
          }}
        >
          No players found
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
            gap: 14,
          }}
        >
          {filtered.map((player) => (
            <PlayerCard
              key={player.id}
              player={player}
              team={teams[player.teamAbbr]}
              onClick={(id) => navigate(`/players/${id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
