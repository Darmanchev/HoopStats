import { useState } from "react";
import type { UpcomingGame } from "./types";
import { useGames } from "./hooks/useGames";
import { useTeams } from "./hooks/useTeams";
import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import Schedule from "./pages/Schedule";
import MatchDetail from "./pages/MatchDetail";

type View = "dashboard" | "schedule" | "detail";

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [selectedGame, setSelectedGame] = useState<UpcomingGame | null>(null);

  const { upcoming, past, loading: matchesLoading } = useGames();
  const { teams, loading: teamsLoading } = useTeams();

  function selectGame(game: UpcomingGame) {
    setSelectedGame(game);
    setView("detail");
  }

  function goBack() {
    setSelectedGame(null);
    setView("dashboard");
  }

  function navigate(v: string) {
    setSelectedGame(null);
    setView(v as View);
  }

  if (matchesLoading || teamsLoading) {
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

  const sidebarActive = view === "detail" ? "dashboard" : view;

  return (
    <Layout active={sidebarActive} onNavigate={navigate}>
      {view === "dashboard" && (
        <Dashboard games={upcoming} teams={teams} onSelect={selectGame} />
      )}
      {view === "schedule" && (
        <Schedule
          upcoming={upcoming}
          past={past}
          teams={teams}
          onSelect={selectGame}
        />
      )}
      {view === "detail" && selectedGame && (
        <MatchDetail
          game={selectedGame}
          teams={teams}
          teamDetails={{}}
          onBack={goBack}
        />
      )}
    </Layout>
  );
}
