import { useSyncExternalStore } from "react";

const KEY = "hoopstats:favorites:v1";
interface Favorites { teams: string[]; players: number[] }
const empty: Favorites = {teams:[],players:[]};
let snapshot: Favorites = empty;
let lastRaw: string | null | undefined;
const listeners = new Set<() => void>();

function read(): Favorites {
  let raw: string | null;
  try { raw = localStorage.getItem(KEY); } catch { return snapshot; }
  if (raw === lastRaw) return snapshot;
  lastRaw = raw;
  try {
    const value = JSON.parse(raw ?? "null");
    snapshot = value?.version === 1 && Array.isArray(value.teams) && Array.isArray(value.players)
      ? {teams:[...new Set<string>(value.teams.filter((v: unknown) => typeof v === "string" && /^[A-Z]{2,5}$/.test(v)))],
         players:[...new Set<number>(value.players.filter((v: unknown) => typeof v === "number" && Number.isSafeInteger(v) && v > 0))]}
      : empty;
  } catch { snapshot = empty; }
  return snapshot;
}
function subscribe(listener: () => void) {
  listeners.add(listener);
  const storage = (event: StorageEvent) => { if (event.key === KEY || event.key === null) listener(); };
  window.addEventListener("storage", storage);
  return () => { listeners.delete(listener); window.removeEventListener("storage", storage); };
}
function update(next: Favorites) {
  snapshot = next;
  const raw = JSON.stringify({version:1,...next});
  try { localStorage.setItem(KEY, raw); lastRaw = raw; } catch { /* keep session favorites */ }
  listeners.forEach(listener => listener());
}
export function useFavorites() {
  const value = useSyncExternalStore(subscribe, read, () => empty);
  return { ...value,
    toggleTeam: (team: string) => { const current = read(); update({...current,teams:current.teams.includes(team) ? current.teams.filter(t => t !== team) : [...current.teams,team]}); },
    togglePlayer: (id: number) => { const current = read(); update({...current,players:current.players.includes(id) ? current.players.filter(p => p !== id) : [...current.players,id]}); },
  };
}
