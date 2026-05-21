import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import type { UpcomingGame, Game } from "../types";
import { useGames } from "../hooks/useGames";
import { useSeasons } from "../hooks/useSeasons";
import { useTeams } from "../hooks/useTeams";
import ScheduleCard from "../components/matches/ScheduleCard";
import { LoadingState, ErrorState } from "../components/ui/PageState";

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

function getDayHeading(dateStr: string): string {
  const d = parseDate(dateStr);
  return `${DAYS[d.getDay()]} · ${MONTHS[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`;
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
  const [season, setSeason] = useState<string>("all");

  const seasons = useSeasons();
  const { upcoming, past, loading: gamesLoading, error: gamesError } = useGames(
    season === "all" ? undefined : season
  );
  const { teams, loading: teamsLoading, error: teamsError } = useTeams();

  const all: Game[] = useMemo(
    // по убыванию даты — последние матчи сверху
    () => [...past, ...upcoming].sort((a, b) => (a.date < b.date ? 1 : -1)),
    [past, upcoming]
  );

  const availableMonths = useMemo(() => {
    const set = new Set<string>();
    all.forEach((g) => set.add(getMonthKey(g.date)));
    return Array.from(set).sort();
  }, [all]);

  const filtered = useMemo(() => {
    return all.filter((g) => {
      // Тип игры — это ещё одно условие, а не ранний выход:
      // раньше `return` обрывал фильтр и игнорировал сезон/месяц/день.
      const isResult = "score1" in g;
      if (typeFilter === "results" && !isResult) return false;
      if (typeFilter === "upcoming" && isResult) return false;
      if (seasonFilter !== "all" && g.seasonType !== seasonFilter) return false;
      if (monthFilter !== "all" && getMonthKey(g.date) !== monthFilter) return false;
      if (dayFilter !== "all" && getDayLabel(g.date) !== dayFilter) return false;
      return true;
    });
  }, [all, typeFilter, seasonFilter, monthFilter, dayFilter]);

  const grouped = useMemo(() => {
    const groups: Record<string, Game[]> = {};
    filtered.forEach((g) => {
      // ключ — сама дата (YYYY-MM-DD): сортируема и уникальна на день
      if (!groups[g.date]) groups[g.date] = [];
      groups[g.date].push(g);
    });
    return groups;
  }, [filtered]);

  if (gamesLoading || teamsLoading) return <LoadingState />;
  if (gamesError || teamsError)
    return <ErrorState message={gamesError || teamsError || ""} />;

  const selectCls =
    "px-3 py-[7px] rounded-[7px] text-xs border border-line text-ink bg-surface cursor-pointer shrink-0";

  return (
    <div className="px-6 sm:px-11 py-9 max-w-[1100px] mx-auto">
      <header className="mb-5">
        <h1 className="font-display font-extrabold text-[26px] tracking-wide uppercase">
          Schedule
        </h1>
        <p className="text-[13px] text-muted mt-1">
          {season === "all" ? "All seasons" : `${season} NBA Season`} ·{" "}
          {filtered.length} games
        </p>
      </header>

      {/* фильтры — одна строка, при нехватке ширины прокручивается по горизонтали */}
      <div className="flex gap-2.5 mb-6 items-center flex-nowrap overflow-x-auto pb-1">
        <div className="flex gap-1 shrink-0">
          {(["all", "upcoming", "results"] as TypeFilter[]).map((f) => (
            <button
              key={f}
              onClick={() => setTypeFilter(f)}
              className={`px-3.5 py-[7px] rounded-[7px] text-[11px] font-bold tracking-wide
                          uppercase cursor-pointer transition-colors ${
                            typeFilter === f
                              ? "bg-brand border border-brand text-white"
                              : "bg-transparent border border-line text-muted hover:border-line-strong hover:text-ink"
                          }`}
            >
              {f}
            </button>
          ))}
        </div>

        <div className="flex gap-1 shrink-0">
          {(["all", "regular", "playoffs"] as SeasonFilter[]).map((s) => (
            <button
              key={s}
              onClick={() => setSeasonFilter(s)}
              className={`px-3.5 py-[7px] rounded-[7px] text-[11px] font-bold tracking-wide
                          cursor-pointer transition-colors ${
                            seasonFilter === s
                              ? "bg-info border border-info text-white"
                              : "bg-transparent border border-line text-muted hover:border-line-strong hover:text-ink"
                          }`}
            >
              {seasonLabels[s]}
            </button>
          ))}
        </div>

        <select
          value={season}
          onChange={(e) => {
            setSeason(e.target.value);
            setMonthFilter("all"); // месяцы зависят от сезона
          }}
          className={selectCls}
        >
          <option value="all">All seasons</option>
          {seasons.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <select
          value={monthFilter}
          onChange={(e) => setMonthFilter(e.target.value)}
          className={selectCls}
        >
          <option value="all">All months</option>
          {availableMonths.map((m) => {
            const [y, mo] = m.split("-");
            return (
              <option key={m} value={m}>
                {MONTHS[parseInt(mo) - 1]} {y}
              </option>
            );
          })}
        </select>

        <select
          value={dayFilter}
          onChange={(e) => setDayFilter(e.target.value)}
          className={selectCls}
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
            className="px-3 py-[7px] rounded-[7px] text-[11px] font-bold cursor-pointer shrink-0
                       bg-transparent border border-line text-muted hover:border-line-strong hover:text-ink transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* список, сгруппированный по месяцам */}
      {Object.keys(grouped).length === 0 ? (
        <div className="text-center py-12 text-faint">No games found</div>
      ) : (
        Object.entries(grouped).map(([day, games]) => (
          <div key={day} className="mb-7">
            <div className="flex items-baseline gap-2.5 mb-3 pl-1">
              <div className="font-display font-bold text-base tracking-wide text-faint uppercase">
                {getDayHeading(day)}
              </div>
              <div className="text-xs text-faint">{games.length} games</div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {games.map((g) => (
                <ScheduleCard
                  key={g.id}
                  game={g}
                  team1={teams[g.team1]}
                  team2={teams[g.team2]}
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
