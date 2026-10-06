import { useEffect, useId, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getSearch, type SearchResults } from "../../lib/api";
import { errorMessage } from "../../hooks/useRemote";

export default function GlobalSearch() {
  const navigate = useNavigate();
  const listId = useId();
  const [query,setQuery] = useState("");
  const [open,setOpen] = useState(false);
  const [active,setActive] = useState(-1);
  const [result,setResult] = useState<{query:string;data?:SearchResults;error?:string}>();
  const term = query.trim();
  useEffect(() => {
    if (term.length < 2) return;
    let cancelled = false;
    const timer = window.setTimeout(() => {
      getSearch(term).then(data => {if (!cancelled) setResult({query:term,data});}, error => {if (!cancelled) setResult({query:term,error:errorMessage(error)});});
    },250);
    return () => {cancelled = true; window.clearTimeout(timer);};
  },[term]);
  const current = result?.query === term ? result : undefined;
  const entries = current?.data ? Object.entries(current.data).flatMap(([group,items]) => items.map(item => ({...item,group}))) : [];
  const shown = open && term.length >= 2;
  function select(index:number) { const item = entries[index]; if (item) {navigate(item.url);setOpen(false);setQuery("");setActive(-1);} }
  return <div className="relative min-w-0 w-full max-w-[360px]" onBlur={event => {if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);}}>
    <div className="flex gap-1"><input role="combobox" aria-label="Search games, teams and players" aria-expanded={shown} aria-controls={listId} aria-autocomplete="list" aria-activedescendant={shown && active >= 0 && entries[active] ? `${listId}-${active}` : undefined}
      maxLength={100} placeholder="Search teams, players, games…" value={query} className="w-full min-w-0 px-3 py-2 border border-line rounded-lg bg-surface-2 text-sm text-ink"
      onFocus={() => setOpen(true)} onChange={event => {setQuery(event.target.value);setOpen(true);setActive(-1);}}
      onKeyDown={event => {
        if (event.key === "Escape") {setOpen(false);setActive(-1);}
        if (event.key === "ArrowDown" || event.key === "ArrowUp") {event.preventDefault();setOpen(true);setActive(i => entries.length ? (i + (event.key === "ArrowDown" ? 1 : -1) + entries.length) % entries.length : -1);}
        if (event.key === "Enter" && shown) {event.preventDefault();select(active >= 0 ? active : 0);}
      }}/>{query && <button aria-label="Clear search" onClick={() => {setQuery("");setActive(-1);}}>×</button>}</div>
    {shown && <div className="absolute top-full left-0 right-0 z-50 bg-surface border border-line rounded-xl shadow-lg mt-2 max-h-[420px] overflow-auto">
      <div id={listId} role="listbox" aria-label="Search results">
        {!current ? <p role="status" className="p-3 text-sm">Searching…</p> : current.error ? <p role="alert" className="p-3 text-sm">{current.error}</p> : !entries.length ? <p className="p-3 text-sm">No results</p> : entries.map((item,index) => <button key={`${item.group}:${item.id}`} id={`${listId}-${index}`} role="option" aria-selected={active === index} className={`w-full text-left p-3 text-sm ${index === active ? "bg-hover" : ""}`} onMouseDown={event => event.preventDefault()} onClick={() => select(index)}>
          <span className="block text-xs text-muted capitalize">{item.group}</span>{item.label}
        </button>)}
      </div>
    </div>}
  </div>;
}
