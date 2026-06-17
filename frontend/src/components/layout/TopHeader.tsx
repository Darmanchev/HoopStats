import { useState } from "react";
import ThemeToggle from "../ui/ThemeToggle";

export default function TopHeader() {
  const [search, setSearch] = useState("");

  return (
    <header className="h-[72px] bg-surface border-b border-line px-6 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-2">
        <div className="font-display font-black text-[23px] tracking-[2.5px] uppercase text-ink">
          Hoop<span className="text-brand">Stats</span>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="hidden md:flex relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-muted">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
          </div>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search Games, Teams, Players..."
            className="w-[280px] h-[40px] pl-10 pr-4 bg-surface-2 border border-line rounded-full text-[13px] text-ink placeholder-faint focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-all"
          />
        </div>

        <ThemeToggle />
      </div>
    </header>
  );
}
