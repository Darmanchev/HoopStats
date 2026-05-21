interface Props {
  data: number[];
  color: string;
  width?: number;
  height?: number;
  /** Подписывать каждую точку её значением. */
  showValues?: boolean;
}

export default function Sparkline({
  data,
  color,
  width = 180,
  height = 48,
  showValues = false,
}: Props) {
  if (!data || data.length < 2) return null;
  const max = Math.max(...data),
    min = Math.min(...data),
    rng = max - min || 1;
  const p = 6;
  // при подписях резервируем место сверху, чтобы цифры не обрезались
  const topPad = showValues ? 18 : p;
  const pts = data.map((v, i) => [
    p + (i / (data.length - 1)) * (width - p * 2),
    topPad + (1 - (v - min) / rng) * (height - topPad - p),
  ]);
  const d = pts
    .map((pt, i) => `${i ? "L" : "M"}${pt[0].toFixed(1)},${pt[1].toFixed(1)}`)
    .join(" ");
  const fill = `${d} L${pts[pts.length - 1][0]},${height} L${pts[0][0]},${height} Z`;
  const last = pts[pts.length - 1];
  const gradId = `sg-${color.replace(/[^a-z0-9]/gi, "")}`;

  return (
    <svg width={width} height={height} className="overflow-visible block">
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={fill} fill={`url(#${gradId})`} />
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth="1.8"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <circle cx={last[0]} cy={last[1]} r={3.5} fill={color} />
      {showValues &&
        pts.map((pt, i) => (
          <text
            key={i}
            x={pt[0]}
            y={pt[1] - 7}
            textAnchor="middle"
            fontSize="10"
            fontWeight="700"
            className={i === pts.length - 1 ? "fill-ink" : "fill-faint"}
          >
            {data[i]}
          </text>
        ))}
    </svg>
  );
}
