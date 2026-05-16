import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import type { UpcomingGame, Game } from "../types";
import { useGames } from "../hooks/useGames";
import { useTeams } from "../hooks/useTeams";
import ScheduleRow from "../components/matches/ScheduleRow";

type TypeFilter = "all" | "upcoming" | "results";
type SeasonFilter = "all" | "regular" | "playoffs";

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function parseDate(dateStr: string): Date {
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? new Date() : d;
}

function getMonthKey(dateStr: string): string {
  const d = parseDate(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function getMonthLabel(dateStr: string): string {
  const d = parseDate(dateStr);
  return `${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

function getDayLabel(dateStr: string): string {
  const d = parseDate(dateStr);
  return DAYS[d.getDay()];
}

const seasonLabels: Record<string, string> = {
  all: "All",
  regular: "Regular Season",
  playoffs: "Playoffs",
};

export default function Schedule() {
  const navigate = useNavigate();
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [seasonFilter, setSeasonFilter] = useState<SeasonFilter>("all");
  const [monthFilter, setMonthFilter] = useState<string>("all");
  const [dayFilter, setDayFilter] = useState<string>("all");

  const { upcoming, past, loading: gamesLoading, error: gamesError } = useGames();
  const { teams, loading: teamsLoading, error: teamsError } = useTeams();

  const all: Game[] = useMemo(
    () => [...past, ...upcoming].sort((a, b) => (a.date > b.date ? 1 : -1)),
    [past, upcoming]
  );

  const availableMonths = useMemo(() => {
    const set = new Set<string>();
    all.forEach((g) => set.add(getMonthKey(g.date)));
    return Array.from(set).sort();
  }, [all]);

  const filtered = useMemo(() => {
    return all.filter((g) => {
      if (typeFilter === "results") return "score1" in g;
      if (typeFilter === "upcoming") return !("score1" in g);
      if (seasonFilter !== "all" && g.seasonType !== seasonFilter) return false;
      if (monthFilter !== "all" && getMonthKey(g.date) !== monthFilter) return false;
      if (dayFilter !== "all" && getDayLabel(g.date) !== dayFilter) return false;
      return true;
    });
  }, [all, typeFilter, seasonFilter, monthFilter, dayFilter]);

  const grouped = useMemo(() => {
    const groups: Record<string, Game[]> = {};
    filtered.forEach((g) => {
      const key = getMonthLabel(g.date);
      if (!groups[key]) groups[key] = [];
      groups[key].push(g);
    });
    return groups;
  }, [filtered]);

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
    <div style={{ padding: "36px 44px", maxWidth: 900, margin: "0 auto" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          marginBottom: 20,
        }}
      >
        <div>
          <div
            style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontWeight: 800,
              fontSize: 26,
              letterSpacing: 1.5,
              textTransform: "uppercase",
            }}
          >
            Schedule
          </div>
          <div style={{ fontSize: 13, color: "#6B7590", marginTop: 4 }}>
            2025–26 NBA Season · {filtered.length} games
          </div>
        </div>
      </div>

      {/* Filters */}
      <div
        style={{
          display: "flex",
          gap: 10,
          marginBottom: 24,
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        {/* Type filter */}
        <div style={{ display: "flex", gap: 4 }}>
          {(["all", "upcoming", "results"] as TypeFilter[]).map((f) => (
            <button
              key={f}
              onClick={() => {
                setTypeFilter(f);
              }}
              style={{
                padding: "7px 14px",
                borderRadius: 7,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1,
                textTransform: "uppercase",
                cursor: "pointer",
                fontFamily: "'Barlow',sans-serif",
                background: typeFilter === f ? "oklch(0.55 0.18 25)" : "transparent",
                border: `1px solid ${typeFilter === f ? "oklch(0.55 0.18 25)" : "#E4E8F2"}`,
                color: typeFilter === f ? "#fff" : "#6B7590",
              }}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Season filter */}
        <div style={{ display: "flex", gap: 4 }}>
          {(["all", "regular", "playoffs"] as SeasonFilter[]).map((s) => (
            <button
              key={s}
              onClick={() => setSeasonFilter(s)}
              style={{
                padding: "7px 14px",
                borderRadius: 7,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1,
                cursor: "pointer",
                fontFamily: "'Barlow',sans-serif",
                background: seasonFilter === s ? "oklch(0.45 0.15 220)" : "transparent",
                border: `1px solid ${seasonFilter === s ? "oklch(0.45 0.15 220)" : "#E4E8F2"}`,
                color: seasonFilter === s ? "#fff" : "#6B7590",
              }}
            >
              {seasonLabels[s]}
            </button>
          ))}
        </div>

        {/* Month filter */}
        <select
          value={monthFilter}
          onChange={(e) => setMonthFilter(e.target.value)}
          style={{
            padding: "7px 12px",
            borderRadius: 7,
            fontSize: 12,
            fontFamily: "'Barlow',sans-serif",
            border: "1px solid #E4E8F2",
            color: "#1C2235",
            background: "#fff",
            cursor: "pointer",
          }}
        >
          <option value="all">All months</option>
          {availableMonths.map((m) => {
            const [y, mo] = m.split("-");
            const label = `${MONTHS[parseInt(mo) - 1]} ${y}`;
            return (
              <option key={m} value={m}>
                {label}
              </option>
            );
          })}
        </select>

        {/* Day filter */}
        <select
          value={dayFilter}
          onChange={(e) => setDayFilter(e.target.value)}
          style={{
            padding: "7px 12px",
            borderRadius: 7,
            fontSize: 12,
            fontFamily: "'Barlow',sans-serif",
            border: "1px solid #E4E8F2",
            color: "#1C2235",
            background: "#fff",
            cursor: "pointer",
          }}
        >
          <option value="all">All days</option>
          {DAYS.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>

        {(monthFilter !== "all" || dayFilter !== "all" || seasonFilter !== "all") && (
          <button
            onClick={() => {
              setMonthFilter("all");
              setDayFilter("all");
              setSeasonFilter("all");
            }}
            style={{
              padding: "7px 12px",
              borderRadius: 7,
              fontSize: 11,
              fontWeight: 700,
              cursor: "pointer",
              fontFamily: "'Barlow',sans-serif",
              background: "transparent",
              border: "1px solid #E4E8F2",
              color: "#6B7590",
            }}
          >
            Clear
          </button>
        )}
      </div>

      {/* Grouped by month */}
      {Object.keys(grouped).length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "48px 0",
            color: "#8A94AE",
            fontFamily: "'Barlow',sans-serif",
          }}
        >
          No games found
        </div>
      ) : (
        Object.entries(grouped).map(([monthLabel, games]) => (
          <div key={monthLabel} style={{ marginBottom: 28 }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                marginBottom: 10,
                paddingLeft: 4,
              }}
            >
              <div
                style={{
                  fontFamily: "'Barlow Condensed',sans-serif",
                  fontWeight: 700,
                  fontSize: 16,
                  letterSpacing: 1.5,
                  color: "#8A94AE",
                  textTransform: "uppercase",
                }}
              >
                {monthLabel}
              </div>
              {games[0]?.seasonType && (
                <span
                  style={{
                    padding: "2px 8px",
                    borderRadius: 4,
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: 0.5,
                    background: games[0].seasonType === "playoffs" ? "#FEF3C7" : "#DBEAFE",
                    color: games[0].seasonType === "playoffs" ? "#92400E" : "#1E40AF",
                    textTransform: "uppercase",
                  }}
                >
                  {games[0].seasonType === "playoffs" ? "Playoffs" : "Regular"}
                </span>
              )}
            </div>
            <div
              style={{
                background: "#FFFFFF",
                border: "1px solid #1C2235",
                borderRadius: 14,
                overflow: "hidden",
              }}
            >
              {games.map((g, idx) => (
                <ScheduleRow
                  key={g.id}
                  game={g}
                  team1={teams[g.team1]}
                  team2={teams[g.team2]}
                  isLast={idx === games.length - 1}
                  onSelect={(game: UpcomingGame) => navigate(`/match/${game.id}`)}
                />
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
