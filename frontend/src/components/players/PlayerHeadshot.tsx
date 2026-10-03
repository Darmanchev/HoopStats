import { useState } from "react";

interface Props {
  nbaId: number | null;
  name: string;
  className?: string;
}

export default function PlayerHeadshot({ nbaId, name, className = "" }: Props) {
  const source = nbaId && nbaId > 0 ? `https://cdn.nba.com/headshots/nba/latest/1040x760/${nbaId}.png` : null;
  const [failedSource, setFailedSource] = useState<string | null>(null);
  const initials = name.trim().split(/\s+/).filter(Boolean).map((part) => part[0]).slice(0, 2).join("");
  return (
    <div className={`relative overflow-hidden bg-surface-2 ${className}`}>
      <span role="img" aria-hidden={Boolean(source && source !== failedSource)} aria-label={`${name} photo unavailable`} className="absolute inset-0 flex items-center justify-center font-display text-3xl font-bold text-faint">
        {initials}
      </span>
      {source && source !== failedSource && <img
        src={source} alt={name} loading="lazy" decoding="async"
        onError={() => setFailedSource(source)}
        className="absolute inset-0 w-full h-full object-cover object-top bg-surface-2"
      />}
    </div>
  );
}
