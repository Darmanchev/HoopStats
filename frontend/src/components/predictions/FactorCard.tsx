import type { Factor, Team } from "../../types";

interface Props {
  factor: Factor;
  team1: Team;
  team2: Team;
}

export default function FactorCard({ factor, team1, team2 }: Props) {
  const edge = factor.invert
    ? factor.val1 < factor.val2
      ? 1
      : factor.val1 > factor.val2
        ? 2
        : 0
    : factor.val1 > factor.val2
      ? 1
      : factor.val1 < factor.val2
        ? 2
        : 0;
  return (
    <div
      style={{
        background: "#F8F9FC",
        border: "1px solid #181E2C",
        borderRadius: 10,
        padding: "16px 18px",
      }}
    >
      <div
        style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: 1.4,
          color: "#8A94AE",
          textTransform: "uppercase",
          marginBottom: 12,
        }}
      >
        {factor.label}
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
        }}
      >
        <div>
          <div
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 800,
              fontSize: 30,
              color: edge === 1 ? team1.accent : "#2A3248",
            }}
          >
            {factor.val1}
          </div>
          {edge === 1 && (
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                color: team1.accent,
                letterSpacing: 1,
              }}
            >
              ▲ EDGE
            </div>
          )}
        </div>
        <div style={{ textAlign: "right" }}>
          <div
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 800,
              fontSize: 30,
              color: edge === 2 ? team2.accent : "#2A3248",
            }}
          >
            {factor.val2}
          </div>
          {edge === 2 && (
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                color: team2.accent,
                letterSpacing: 1,
                textAlign: "right",
              }}
            >
              ▲ EDGE
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
