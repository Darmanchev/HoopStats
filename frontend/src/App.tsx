import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import Schedule from "./pages/Schedule";
import MatchDetail from "./pages/MatchDetail";
import Teams from "./pages/Teams";
import TeamDetail from "./pages/TeamDetail";
import Injuries from "./pages/Injuries";
import Players from "./pages/Players";
import PlayerDetail from "./pages/PlayerDetail";
import Analytics from "./pages/Analytics";
import ErrorPage from "./pages/ErrorPage";
import ErrorBoundary from "./components/ui/ErrorBoundary";

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="schedule" element={<Schedule />} />
            <Route path="match/:id" element={<MatchDetail />} />
            <Route path="teams" element={<Teams />} />
            <Route path="teams/:abbr" element={<TeamDetail />} />
            <Route path="players" element={<Players />} />
            <Route path="players/:id" element={<PlayerDetail />} />
            <Route path="injuries" element={<Injuries />} />
            <Route path="analytics" element={<Analytics />} />
          </Route>
          <Route path="*" element={<ErrorPage />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
