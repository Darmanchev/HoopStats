interface Props {
  r: "W" | "L";
}

export default function FormBadge({ r }: Props) {
  const win = r === "W";
  return (
    <span
      style={{
        width: 26,
        height: 26,
        borderRadius: 5,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        background: win ? "oklch(0.88 0.08 145)" : "oklch(0.90 0.06 15)",
        color: win ? "oklch(0.28 0.14 145)" : "oklch(0.32 0.12 15)",
        fontFamily: "'Barlow Condensed',sans-serif",
        fontWeight: 800,
        fontSize: 13,
      }}
    >
      {r}
    </span>
  );
}
