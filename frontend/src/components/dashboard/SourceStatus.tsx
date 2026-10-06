import { useState } from "react";
import { retrySync, type SyncSourceStatus } from "../../lib/api";

const groups = [
  { label: "Scores", matches: (name: string) => /games|schedule|box_scores|historical/.test(name) },
  { label: "Player statistics", matches: (name: string) => /player/.test(name) },
  { label: "Predictions", matches: (name: string) => /prediction/.test(name) },
];
const sourceLabel = (name: string) => name.replace(/^sync_/, "").replaceAll("_", " ");
function timestamp(value?: string) {
  if (!value) return "No successful import recorded";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Import date unavailable" : date.toLocaleString();
}
export default function SourceStatus({ statuses, unavailable, onQueued }: {
  statuses: Record<string, SyncSourceStatus>; unavailable: boolean; onQueued: () => unknown;
}) {
  const [token, setToken] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const entries = Object.entries(statuses);
  const failed = entries.filter(([, status]) => status.state === "failed");
  async function retry(source: string) {
    setPending(source);
    setMessage("");
    const accessToken = token;
    setToken("");
    try {
      await retrySync(source, accessToken);
      setMessage(`Retry queued for ${sourceLabel(source)}. Import completion will appear after the next check.`);
      void onQueued();
    } catch (reason) {
      const status = reason && typeof reason === "object" && "status" in reason ? reason.status : 0;
      setMessage(status === 403 ? "Retry access denied. Check the access token and server configuration." : status === 409 ? "This import is already queued or running." : "Retry could not be queued. Check your connection and try again.");
    } finally { setPending(null); }
  }
  return <section aria-label="Import status" className="mb-5 rounded-xl border border-line bg-surface p-4">
    <h2 className="font-semibold mb-2">Latest successful imports</h2>
    <p className="text-xs text-muted mb-3">Import times show when source data was saved. Last checked shows when this page refreshed.</p>
    {unavailable && <p role="status" className="text-sm mb-3">Import status unavailable. Displayed import times may be outdated.</p>}
    <div className="grid gap-3 sm:grid-cols-3">{groups.map(group => {
      const sources = entries.filter(([name]) => group.matches(name));
      return <div key={group.label}><h3 className="font-semibold text-sm">{group.label}</h3>{sources.length ? sources.map(([name, status]) => <p key={name} className="text-xs text-muted mt-1"><span>{sourceLabel(name)}: </span>{timestamp(status.last_success)}{status.state === "running" && " · Updating"}{status.state === "failed" && " · Update failed"}</p>) : <p className="text-xs text-muted mt-1">No successful import recorded</p>}</div>;
    })}</div>
    {!!failed.length && <div className="mt-4 border-t border-line pt-3">
      <p className="text-sm font-semibold mb-2">Failed imports</p>
      <label className="text-xs" htmlFor="sync-token">Import access token</label>
      <input id="sync-token" type="password" autoComplete="off" value={token} onChange={event => setToken(event.target.value)} className="block rounded-lg border border-line bg-surface px-3 py-2 mt-1 mb-2 w-full sm:max-w-sm" />
      <p className="text-xs text-muted mb-2">Enter the operator token to retry. It is cleared after each request.</p>
      {failed.map(([name]) => <div key={name} className="flex flex-wrap items-center gap-2 mt-2"><span className="text-sm">{sourceLabel(name)} · Update failed</span><button disabled={!token || pending !== null} onClick={() => void retry(name)} className="rounded-lg border border-line px-3 py-2 text-xs disabled:opacity-50">{pending === name ? "Queuing…" : `Retry ${sourceLabel(name)}`}</button></div>)}
    </div>}
    {message && <p role="status" className="text-sm mt-3">{message}</p>}
  </section>;
}
