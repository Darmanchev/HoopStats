import type { Team, TeamStats } from "../../types";
import FormBadge from "../teams/FormBadge";
import TeamLogo from "../teams/TeamLogo";

interface Props {
  team: Team;
  stats?: TeamStats;
  onClick: (abbr: string) => void;
}

export default function TeamCard({ team, stats, onClick }: Props) {
  const wins = parseInt(team.record.split("-")[0]) || 0;
  const losses = parseInt(team.record.split("-")[1]) || 0;
  const winPct = wins + losses > 0 ? (wins / (wins + losses) * 100).toFixed(1) : "0.0";

  return (
    <div
      onClick={() => onClick(team.abbr)}
      style={{
        background: "#FFFFFF",
        border: "1px solid #1C2235",
        borderRadius: 14,
        padding: "22px 24px",
        cursor: "pointer",
        transition: "all 0.15s ease",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow = "0 8px 32px rgba(0,0,0,0.4)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "none";
        e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.2)";
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
        <TeamLogo team={team} abbr={team.abbr} size={48} />
        <div>
          <div
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 800,
              fontSize: 20,
            }}
          >
            {team.city}{" "}
            <span style={{ color: team.accent }}>{team.name}</span>
          </div>
          <div style={{ fontSize: 13, color: "#6B7590" }}>
            {team.record} · {winPct}%
          </div>
        </div>
      </div>

      {stats && stats.form.length > 0 && (
        <div>
          <div
            style={{
              fontSize: 10,
              letterSpacing: 1.2,
              color: "#8A94AE",
              fontWeight: 700,
              marginBottom: 6,
            }}
          >
            LAST 5
          </div>
          <div style={{ display: "flex", gap: 5 }}>
            {stats.form.map((r: string, i: number) => (
              <FormBadge key={i} r={r as "W" | "L"} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
