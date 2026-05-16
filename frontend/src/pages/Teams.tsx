import { useNavigate } from "react-router-dom";
import { useAllTeams } from "../hooks/useAllTeams";
import TeamCard from "../components/teams/TeamCard";
import { useState } from "react";

type SortBy = "name" | "record" | "abbr";

export default function Teams() {
  const navigate = useNavigate();
  const { teams, stats, loading, error } = useAllTeams();
  const [sortBy, setSortBy] = useState<SortBy>("record");
  const [search, setSearch] = useState("");

  const sorted = [...teams].sort((a, b) => {
    if (sortBy === "record") {
      const wa = parseInt(a.record.split("-")[0]) || 0;
      const wb = parseInt(b.record.split("-")[0]) || 0;
      return wb - wa;
    }
    if (sortBy === "name") return a.name.localeCompare(b.name);
    return a.abbr.localeCompare(b.abbr);
  });

  const filtered = sorted.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.city.toLowerCase().includes(search.toLowerCase()) ||
      t.abbr.toLowerCase().includes(search.toLowerCase())
  );

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
          NBA Teams
        </div>
        <div style={{ fontSize: 13, color: "#6B7590", marginTop: 4 }}>
          {filtered.length} teams
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
          placeholder="Search teams..."
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
          {(["record", "name", "abbr"] as SortBy[]).map((s) => (
            <button
              key={s}
              onClick={() => setSortBy(s)}
              style={{
                padding: "7px 14px",
                borderRadius: 7,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1,
                textTransform: "uppercase",
                cursor: "pointer",
                fontFamily: "'Barlow',sans-serif",
                background: sortBy === s ? "oklch(0.55 0.18 25)" : "transparent",
                border: `1px solid ${sortBy === s ? "oklch(0.55 0.18 25)" : "#E4E8F2"}`,
                color: sortBy === s ? "#fff" : "#6B7590",
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
          gap: 14,
        }}
      >
        {filtered.map((team) => (
          <TeamCard
            key={team.abbr}
            team={team}
            stats={stats[team.abbr]}
            onClick={(abbr) => navigate(`/teams/${abbr}`)}
          />
        ))}
      </div>
    </div>
  );
}
