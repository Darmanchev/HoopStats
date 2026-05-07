import type { Team } from "../../types";

interface Props {
  team: Team; // объект команды — цвета, название
  abbr: string; // аббревиатура — LAL, BOS — она же текст внутри круга
  size?: number; // необязательный, по умолчанию 48
}

export default function TeamLogo({ team, abbr, size = 48 }: Props) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: team.color,
        border: `2px solid ${team.accent}33`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Barlow Condensed',sans-serif",
        fontWeight: 800,
        fontSize: size * 0.32,
        color: team.accent,
        letterSpacing: "0.5px",
        flexShrink: 0,
      }}
    >
      {abbr}
    </div>
  );
}
