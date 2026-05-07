import type { Injury } from "../../types";

interface Props {
  status: Injury["status"];
}

export default function StatusPill({ status }: Props) {
  const map: Record<Injury["status"], [string, string]> = {
    Out: ["oklch(0.92 0.06 12)", "oklch(0.28 0.14 12)"],
    Doubtful: ["oklch(0.92 0.06 40)", "oklch(0.30 0.12 40)"],
    Questionable: ["oklch(0.92 0.05 75)", "oklch(0.28 0.12 75)"],
    "Day-to-Day": ["oklch(0.92 0.04 210)", "oklch(0.26 0.10 210)"],
  };
  const [bg, fg] = map[status];
  return (
    <span
      style={{
        padding: "3px 9px",
        borderRadius: 4,
        fontSize: 11,
        fontWeight: 600,
        background: bg,
        color: fg,
        whiteSpace: "nowrap",
      }}
    >
      {status}
    </span>
  );
}
