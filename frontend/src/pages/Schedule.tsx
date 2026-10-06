import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGameSeasons } from "../hooks/useSeasons";
import { useTeams } from "../hooks/useTeams";
import { useFavorites } from "../hooks/useFavorites";
import { useRemote } from "../hooks/useRemote";
import { getSchedule, getScheduleMonths } from "../lib/api";
import ScheduleCard from "../components/matches/ScheduleCard";
import { LoadingState } from "../components/ui/PageState";

export default function Schedule() {
  const navigate = useNavigate();
  const {seasons,loading:seasonsLoading,error:seasonsError,retry:retrySeasons} = useGameSeasons();
  const {teams} = useTeams();
  const favorites = useFavorites();
  const [filters, setFilters] = useState({season:"",status:"all",type:"all",month:"all",weekday:"all",favorites:false,page:0,pageTeams:""});
  const season = filters.season || seasons[0];
  const selected = season === "all" ? undefined : season;
  const favoriteTeams = favorites.teams.join(",");
  const page = filters.favorites && filters.pageTeams !== favoriteTeams ? 0 : filters.page;
  const emptyFavorites = filters.favorites && !favoriteTeams;
  const load = useCallback(() => {
    let dateTo: string | undefined;
    if (filters.month !== "all") {
      const [year,month] = filters.month.split("-").map(Number);
      dateTo = `${filters.month}-${new Date(Date.UTC(year,month,0)).getUTCDate()}`;
    }
    return emptyFavorites ? Promise.resolve({items:[],total:0}) : getSchedule({
      season:selected,status:filters.status === "all" ? undefined : filters.status,
      season_type:filters.type === "all" ? undefined : filters.type,
      date_from:filters.month === "all" ? undefined : `${filters.month}-01`,date_to:dateTo,
      weekday:filters.weekday === "all" ? undefined : Number(filters.weekday),
      team:filters.favorites ? favoriteTeams : undefined,skip:page * 50,limit:50,
    });
  }, [selected,filters.status,filters.type,filters.month,filters.weekday,filters.favorites,page,emptyFavorites,favoriteTeams]);
  const result = useRemote(season ? JSON.stringify([filters,season,favoriteTeams]) : null, load);
  const loadMonths = useCallback(() => getScheduleMonths(selected), [selected]);
  const months = useRemote(season ? `months:${season}` : null, loadMonths);
  function change(next: Partial<typeof filters>) { setFilters(current => ({...current,...next,page:0})); }
  const cls = "px-3 py-2 rounded-lg border border-line bg-surface text-ink text-sm";
  if (seasonsError) return <div className="p-8" role="alert">{seasonsError} <button onClick={retrySeasons}>Retry</button></div>;
  if (!seasonsLoading && !seasons.length) return <div className="p-8">No game seasons imported</div>;
  return <div className="px-5 sm:px-10 py-8 max-w-[1100px] mx-auto">
    <h1 className="font-display font-extrabold text-2xl mb-2">Schedule</h1>
    <p className="text-muted mb-5">{season === "all" ? "All seasons" : season || "Loading seasons…"} · {result.data?.total ?? 0} games</p>
    <div className="flex flex-wrap gap-2 mb-5">
      <select aria-label="Season" className={cls} value={season ?? ""} onChange={event => change({season:event.target.value,month:"all"})}>
        {!season && <option value="">Loading…</option>}<option value="all">All seasons</option>{seasons.map(s => <option key={s}>{s}</option>)}
      </select>
      <select aria-label="Game status" className={cls} value={filters.status} onChange={event => change({status:event.target.value})}>{[["all","All statuses"],["scheduled","Upcoming"],["live","Live"],["final","Results"]].map(([v,label]) => <option key={v} value={v}>{label}</option>)}</select>
      {[["all","All competitions"],["preseason","Preseason"],["regular","Regular Season"],["playoffs","Playoffs"]].map(([v,label]) => <button key={v} className={cls} aria-pressed={filters.type === v} onClick={() => change({type:v})}>{label}</button>)}
      <select aria-label="Month" className={cls} value={filters.month} onChange={event => change({month:event.target.value})}><option value="all">All months</option>{months.data?.map(m => <option key={m}>{m}</option>)}</select>
      <select aria-label="Weekday" className={cls} value={filters.weekday} onChange={event => change({weekday:event.target.value})}><option value="all">All days</option>{["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].map((day,i) => <option key={day} value={i}>{day}</option>)}</select>
      <button className={cls} aria-pressed={filters.favorites} onClick={() => change({favorites:!filters.favorites})}>Favorite teams</button>
    </div>
    {months.error && <p role="alert">Month choices unavailable <button onClick={months.retry}>Retry</button></p>}
    {result.loading || !season ? <LoadingState/> : result.error ? <p role="alert">{result.error} <button onClick={result.retry}>Retry</button></p> : !result.data?.items.length ? <p className="py-12 text-center text-muted">{emptyFavorites ? "Save a team to filter favorite games" : "No games found"}</p> : <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {result.data.items.map(game => <ScheduleCard key={game.id} game={game}
        team1={teams[game.team1] ?? {abbr:game.team1,name:game.team1,city:"",record:""}}
        team2={teams[game.team2] ?? {abbr:game.team2,name:game.team2,city:"",record:""}}
        onSelect={g => navigate(`/match/${encodeURIComponent(g.id)}`)}/>)}</div>}
    <div className="flex items-center gap-3 mt-6"><button className={cls} disabled={result.loading || page === 0} onClick={() => setFilters(f => ({...f,page:page-1,pageTeams:favoriteTeams}))}>Previous</button><span>Page {page+1}</span><button className={cls} disabled={result.loading || (page+1)*50 >= (result.data?.total ?? 0)} onClick={() => setFilters(f => ({...f,page:page+1,pageTeams:favoriteTeams}))}>Next</button></div>
  </div>;
}
