import { useInjuries } from "../hooks/useInjuries";
import { useState } from "react";

type StatusFilter = "all" | "Out" | "Doubtful" | "Questionable" | "Day-to-Day";

const statusColors: Record<string, { bg: string; text: string }> = {
  Out: { bg: "#FEE2E2", text: "#991B1B" },
  Doubtful: { bg: "#FEF3C7", text: "#92400E" },
  Questionable: { bg: "#DBEAFE", text: "#1E40AF" },
  "Day-to-Day": { bg: "#E0E7FF", text: "#3730A3" },
};

export default function Injuries() {
  const { injuries, loading, error } = useInjuries();
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [search, setSearch] = useState("");

  const filtered = injuries.filter((i) => {
    const matchStatus = filter === "all" || i.status === filter;
    const matchSearch =
      i.playerName.toLowerCase().includes(search.toLowerCase()) ||
      i.teamAbbr.toLowerCase().includes(search.toLowerCase()) ||
      i.injury.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

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
    <div style={{ padding: "36px 44px", maxWidth: 900, margin: "0 auto" }}>
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
          Injury Report
        </div>
        <div style={{ fontSize: 13, color: "#6B7590", marginTop: 4 }}>
          {filtered.length} players
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
          {(["all", "Out", "Doubtful", "Questionable", "Day-to-Day"] as StatusFilter[]).map(
            (f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                style={{
                  padding: "7px 14px",
                  borderRadius: 7,
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: 1,
                  textTransform: "uppercase",
                  cursor: "pointer",
                  fontFamily: "'Barlow',sans-serif",
                  background: filter === f ? "oklch(0.55 0.18 25)" : "transparent",
                  border: `1px solid ${filter === f ? "oklch(0.55 0.18 25)" : "#E4E8F2"}`,
                  color: filter === f ? "#fff" : "#6B7590",
                }}
              >
                {f}
              </button>
            )
          )}
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
          No injuries found
        </div>
      ) : (
        <div
          style={{
            background: "#FFFFFF",
            border: "1px solid #1C2235",
            borderRadius: 14,
            overflow: "hidden",
          }}
        >
          {filtered.map((injury, idx) => {
            const colors = statusColors[injury.status] || { bg: "#F3F4F6", text: "#374151" };
            return (
              <div
                key={`${injury.teamAbbr}-${injury.playerName}-${idx}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  padding: "16px 24px",
                  borderBottom: idx < filtered.length - 1 ? "1px solid #EDF0F8" : "none",
                }}
              >
                <div style={{ width: 50, flexShrink: 0 }}>
                  <span
                    style={{
                      fontFamily: "'Barlow Condensed',sans-serif",
                      fontWeight: 700,
                      fontSize: 16,
                      color: "#1C2235",
                    }}
                  >
                    {injury.teamAbbr}
                  </span>
                </div>

                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      fontFamily: "'Barlow Condensed',sans-serif",
                      fontWeight: 700,
                      fontSize: 16,
                    }}
                  >
                    {injury.playerName}
                  </div>
                  <div style={{ fontSize: 13, color: "#6B7590" }}>
                    {injury.position} · {injury.injury}
                  </div>
                </div>

                <span
                  style={{
                    padding: "4px 12px",
                    borderRadius: 6,
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: 0.5,
                    background: colors.bg,
                    color: colors.text,
                  }}
                >
                  {injury.status}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
