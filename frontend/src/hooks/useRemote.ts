import { useCallback, useEffect, useState } from "react";

export function errorMessage(error: unknown): string {
  return typeof error === "object" && error !== null && "message" in error ? String(error.message) : "Unable to load data";
}

/** Callers provide a stable loader; keyed results never leak across navigation. */
export function useRemote<T>(key: string | null, loader: () => Promise<T>, refresh = 0) {
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState<{ key: string; version: number; data?: T; error?: string }>();
  useEffect(() => {
    if (key === null) return;
    let active = true;
    Promise.resolve().then(loader).then(
      data => { if (active) setResult({key, version, data}); },
      error => { if (active) setResult(previous => ({key, version, data:previous?.key === key ? previous.data : undefined, error:errorMessage(error)})); },
    );
    return () => { active = false; };
  }, [key, loader, version, refresh]);
  const current = result?.key === key && result?.version === version;
  const retry = useCallback(() => setVersion(value => value + 1), []);
  return { data:current ? result?.data : undefined, error:current ? result?.error : undefined, loading:key !== null && !current, retry };
}
