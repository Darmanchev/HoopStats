import type { Team } from "../../types";
import { getTeamColors } from "../../utils/colors";

interface Props {
  team: Team;
  abbr: string;
  size?: number;
}

// ESPN CDN использует другие аббревиатуры для некоторых команд
const ESPN_ABBR: Record<string, string> = {
  UTA: "UTAH",
  NOP: "NO",
};

const NBA_LOGO_URL = (abbr: string) =>
  `https://a.espncdn.com/i/teamlogos/nba/500/${ESPN_ABBR[abbr] || abbr}.png`;

export default function TeamLogo({ team, abbr, size = 48 }: Props) {
  return (
    <img
      src={NBA_LOGO_URL(abbr)}
      alt={`${team.city} ${team.name}`}
      width={size}
      height={size}
      className="shrink-0 object-contain"
      onError={(e) => {
        const target = e.currentTarget;
        target.style.display = "none";
        const fallback = document.createElement("div");
        fallback.style.cssText = `
          width: ${size}px;
          height: ${size}px;
          border-radius: 50%;
          background: ${getTeamColors(abbr).color};
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'Barlow Condensed', sans-serif;
          font-weight: 800;
          font-size: ${size * 0.32}px;
          color: ${getTeamColors(abbr).accent};
        `;
        fallback.textContent = abbr;
        target.parentNode?.appendChild(fallback);
      }}
    />
  );
}
