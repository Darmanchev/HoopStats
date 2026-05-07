import { useState } from "react";
import type { UpcomingGame } from "./types"; // было ./src/types
import { HOOPDATA } from "./data/hoopdata"; // было ./src/data/hoopdata
import Layout from "./components/layout/Layout"; // было ./src/components/...
import Dashboard from "./pages/Dashboard"; // было ./src/pages/...
import Schedule from "./pages/Schedule";
import MatchDetail from "./pages/MatchDetail";

type View = "dashboard" | "schedule" | "detail";

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [selectedGame, setSelectedGame] = useState<UpcomingGame | null>(null);

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

  const sidebarActive = view === "detail" ? "dashboard" : view;

  return (
    <Layout active={sidebarActive} onNavigate={navigate}>
      {view === "dashboard" && (
        <Dashboard
          games={HOOPDATA.UPCOMING}
          teams={HOOPDATA.TEAMS}
          onSelect={selectGame}
        />
      )}
      {view === "schedule" && (
        <Schedule
          upcoming={HOOPDATA.UPCOMING}
          past={HOOPDATA.PAST}
          teams={HOOPDATA.TEAMS}
          onSelect={selectGame}
        />
      )}
      {view === "detail" && selectedGame && (
        <MatchDetail
          game={selectedGame}
          teams={HOOPDATA.TEAMS}
          teamDetails={HOOPDATA.TEAM_DETAILS}
          onBack={goBack}
        />
      )}
    </Layout>
  );
}
