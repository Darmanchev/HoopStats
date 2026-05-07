interface Props {
  data: number[];
  color: string;
  width?: number;
  height?: number;
}

export default function Sparkline({
  data,
  color,
  width = 180,
  height = 48,
}: Props) {
  if (!data || data.length < 2) return null;
  const max = Math.max(...data),
    min = Math.min(...data),
    rng = max - min || 1;
  const p = 6;
  const pts = data.map((v, i) => [
    p + (i / (data.length - 1)) * (width - p * 2),
    p + (1 - (v - min) / rng) * (height - p * 2),
  ]);
  const d = pts
    .map((pt, i) => `${i ? "L" : "M"}${pt[0].toFixed(1)},${pt[1].toFixed(1)}`)
    .join(" ");
  const fill = `${d} L${pts[pts.length - 1][0]},${height} L${pts[0][0]},${height} Z`;
  const last = pts[pts.length - 1];
  return (
    <svg
      width={width}
      height={height}
      style={{ overflow: "visible", display: "block" }}
    >
      <defs>
        <linearGradient
          id={`sg-${color.replace(/[^a-z0-9]/gi, "")}`}
          x1="0"
          y1="0"
          x2="0"
          y2="1"
        >
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={fill} fill={`url(#sg-${color.replace(/[^a-z0-9]/gi, "")})`} />
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth="1.8"
        strokeLinejoin="round"  
        strokeLinecap="round"
      />
      <circle cx={last[0]} cy={last[1]} r={3.5} fill={color} />
    </svg>
  );
}
