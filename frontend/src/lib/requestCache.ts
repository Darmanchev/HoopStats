const entries = new Map<
  string,
  { expiresAt: number; promise: Promise<unknown> }
>();


export function cachedRequest<T>(
  key: string,
  ttlMs: number,
  loader: () => Promise<T>,
): Promise<T> {
  const cached = entries.get(key);
  if (cached && cached.expiresAt > Date.now()) {
    return cached.promise as Promise<T>;
  }

  const promise = loader().catch((error) => {
    entries.delete(key);
    throw error;
  });
  entries.set(key, { expiresAt: Date.now() + ttlMs, promise });
  return promise;
}
