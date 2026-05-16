import { useNavigate } from "react-router-dom";
import { useGames } from "../hooks/useGames";
import { useTeams } from "../hooks/useTeams";
import GameCard from "../components/matches/GameCard";

export default function Dashboard() {
  const navigate = useNavigate();
  const { upcoming, loading: gamesLoading, error: gamesError } = useGames();
  const { teams, loading: teamsLoading, error: teamsError } = useTeams();

  const today = upcoming.filter((g) => g.isToday);
  const future = upcoming.filter((g) => !g.isToday);

  if (gamesLoading || teamsLoading) {
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

  if (gamesError || teamsError) {
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
        {gamesError || teamsError}
      </div>
    );
  }

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
            onClick={() => navigate(`/match/${g.id}`)}
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
        {future.map((g) => (
          <GameCard
            key={g.id}
            game={g}
            team1={teams[g.team1]}
            team2={teams[g.team2]}
            onClick={() => navigate(`/match/${g.id}`)}
          />
        ))}
      </div>
    </div>
  );
}
