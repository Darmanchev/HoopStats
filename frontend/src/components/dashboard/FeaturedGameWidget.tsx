import type { UpcomingGame, Team } from "../../types";
import TeamLogo from "../teams/TeamLogo";

interface Props {
  game: UpcomingGame | null;
  team1: Team | null;
  team2: Team | null;
}

export default function FeaturedGameWidget({ game, team1, team2 }: Props) {
  if (!game || !team1 || !team2) {
    return (
      <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line h-full flex items-center justify-center">
        <span className="text-faint text-sm">No featured game</span>
      </div>
    );
  }

  return (
    <div className="bg-surface rounded-3xl p-6 shadow-[var(--shadow-card)] border border-line flex flex-col h-full">
      <div className="mb-6">
        <h2 className="font-display font-semibold text-[18px] text-ink">Featured Game:</h2>
        <p className="text-[14px] text-muted">{team1.city} {team1.name} vs. {team2.city} {team2.name}</p>
      </div>

      <div className="flex-1 flex flex-col justify-center">
        <div className="flex items-center justify-center gap-6 mb-6">
          <TeamLogo team={team1} abbr={game.team1} size={50} />
          <div className="font-display font-bold text-[42px] tracking-tight text-ink">
            112 - 108
          </div>
          <TeamLogo team={team2} abbr={game.team2} size={50} />
        </div>

        <div className="w-full">
          <div className="flex justify-between items-center mb-2">
            <span className="text-[12px] font-medium text-ink">Live Stats</span>
            <span className="text-[12px] font-bold text-ink">Q4 4:32</span>
          </div>
          <div className="h-2 w-full bg-surface-2 rounded-full overflow-hidden flex">
            <div className="h-full bg-brand w-[60%]"></div>
            <div className="h-full bg-orange-400 w-[20%]"></div>
            <div className="h-full bg-faint w-[10%] opacity-30"></div>
          </div>
        </div>
      </div>

      <div className="mt-6">
        <button className="w-full py-2.5 rounded-full border-2 border-brand text-brand font-semibold text-[14px] hover:bg-brand/5 transition-colors">
          Live Stats
        </button>
      </div>
    </div>
  );
}
