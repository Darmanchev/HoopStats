import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { getModelPerformance, type EvaluationMetrics } from "../../lib/api";
import { useRemote } from "../../hooks/useRemote";

function metric(value:number|null|undefined,percentage=false){return value == null ? "Unavailable" : percentage ? `${(value*100).toFixed(1)}%` : value.toFixed(3);}
export default function ModelPerformance() {
  const [page,setPage] = useState(0);
  const loader = useCallback(()=>getModelPerformance(page*20),[page]);
  const result = useRemote(`performance:${page}`,loader);
  const report = result.data;
  const rows:{label:string;values:EvaluationMetrics}[] = report?.metrics ? [{label:"Logistic model",values:report.metrics},...Object.entries(report.baselines ?? {}).map(([label,values])=>({label:`${label === "elo" ? "Elo" : "Home preference"} baseline`,values}))] : [];
  return <section className="bg-surface border border-line rounded-xl p-5 mt-8">
    <h2 className="font-bold text-lg mb-3">Prediction performance</h2>
    {result.loading ? <p>Loading evaluation…</p> : result.error ? <p role="alert">{result.error} <button onClick={result.retry}>Retry</button></p> : !report?.available ? <p className="text-muted">{report?.reason ?? "Model evaluation unavailable"}</p> : <>
      <p className="text-sm text-muted mb-4">Held-out evaluation · {report.test_season} · {report.n_train} training games · {report.n_test} test games</p>
      <p className="text-xs text-muted mb-4">Trained {report.trained_at ? new Date(report.trained_at).toLocaleString() : "date unavailable"}. These are held-out results; the deployed model is refit on all eligible games.</p>
      <div className="overflow-auto"><table className="w-full text-sm text-left"><thead><tr>{["Model","Accuracy","Log loss ↓","Brier ↓","AUC"].map(h=><th className="p-2" key={h}>{h}</th>)}</tr></thead><tbody>{rows.map(row=><tr key={row.label} className="border-t border-line"><th className="p-2">{row.label}</th><td>{metric(row.values.accuracy,true)}</td><td>{metric(row.values.log_loss)}</td><td>{metric(row.values.brier)}</td><td>{metric(row.values.auc)}</td></tr>)}</tbody></table></div>
      <h3 className="font-bold mt-6 mb-3">Probability calibration</h3><p className="text-sm text-muted mb-3">Compare predicted away-team win probability with the observed win rate in each range.</p>
      <div className="overflow-auto"><table className="w-full text-sm text-left"><thead><tr>{["Probability range","Games","Predicted","Observed"].map(h=><th className="p-2" key={h}>{h}</th>)}</tr></thead><tbody>{report.calibration?.map(bin=><tr key={bin.lower} className="border-t border-line"><td className="p-2">{Math.round(bin.lower*100)}–{Math.round(bin.upper*100)}%</td><td>{bin.count}</td><td>{metric(bin.predicted,true)}</td><td>{metric(bin.observed,true)}</td></tr>)}</tbody></table></div>
      <h3 className="font-bold mt-6 mb-3">Held-out game results</h3><div className="overflow-auto"><table className="w-full text-sm text-left"><thead><tr>{["Date","Matchup","Away win probability","Winner","Correct"].map(h=><th className="p-2" key={h}>{h}</th>)}</tr></thead><tbody>{report.games.map(g=><tr key={g.id} className="border-t border-line"><td className="p-2 whitespace-nowrap">{g.date}</td><td><Link to={`/match/${encodeURIComponent(g.id)}`}>{g.team1} at {g.team2}</Link></td><td>{metric(g.probability,true)}</td><td>{g.actual ? g.team1 : g.team2}</td><td>{g.correct ? "Yes" : "No"}</td></tr>)}</tbody></table></div>
      <div className="flex gap-3 mt-4"><button disabled={page===0} onClick={()=>setPage(p=>p-1)}>Previous</button><span>Page {page+1}</span><button disabled={(page+1)*20>=report.total} onClick={()=>setPage(p=>p+1)}>Next</button></div>
    </>}
  </section>;
}
