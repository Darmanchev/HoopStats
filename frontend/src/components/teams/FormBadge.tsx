interface Props {
  r: "W" | "L";
}

export default function FormBadge({ r }: Props) {
  const win = r === "W";
  return (
    <span
      className={`w-[26px] h-[26px] rounded-md inline-flex items-center justify-center
                  font-display font-extrabold text-[13px] ${
                    win
                      ? "bg-win-bg text-win-fg"
                      : "bg-danger-bg text-danger-fg"
                  }`}
    >
      {r}
    </span>
  );
}
