import type { UpcomingGame, Team } from "../types";
import GameCard from "../components/matches/GameCard";

interface Props {
  games: UpcomingGame[];
  teams: Record<string, Team>;
  onSelect: (game: UpcomingGame) => void;
}

export default function Dashboard({ games, teams, onSelect }: Props) {
  const today = games.filter((g) => g.isToday);
  const upcoming = games.filter((g) => !g.isToday);

  return (
    <div style={{ padding: "36px 44px", maxWidth: 860, margin: "0 auto" }}>
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
          Tonight's Games
        </div>
        <div style={{ fontSize: 13, color: "#6B7590", marginTop: 4 }}>
          April 25, 2026 · NBA Playoffs Round 1
        </div>
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 14,
          marginBottom: 44,
        }}
      >
        {today.map((g) => (
          <GameCard
            key={g.id}
            game={g}
            team1={teams[g.team1]}
            team2={teams[g.team2]}
            onClick={onSelect}
          />
        ))}
      </div>

      <div
        style={{
          fontFamily: "'Barlow Condensed',sans-serif",
          fontWeight: 700,
          fontSize: 14,
          letterSpacing: 1.6,
          color: "#8A94AE",
          textTransform: "uppercase",
          marginBottom: 14,
        }}
      >
        Upcoming
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {upcoming.map((g) => (
          <GameCard
            key={g.id}
            game={g}
            team1={teams[g.team1]}
            team2={teams[g.team2]}
            onClick={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
