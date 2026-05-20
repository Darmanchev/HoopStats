import { useState } from "react";
import { NavLink } from "react-router-dom";
import ThemeToggle from "../ui/ThemeToggle";

const nav = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z",
    to: "/",
  },
  {
    id: "schedule",
    label: "Schedule",
    icon: "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 002 2v12a2 2 0 002 2z",
    to: "/schedule",
  },
  {
    id: "teams",
    label: "Teams",
    icon: "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2",
    to: "/teams",
  },
  {
    id: "players",
    label: "Players",
    icon: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
    to: "/players",
  },
  {
    id: "injuries",
    label: "Injuries",
    icon: "M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
    to: "/injuries",
  },
];

const soon = ["Analytics"];

export default function Sidebar() {
  // на десктопе сайдбар всегда виден, на мобильных управляется этим стейтом
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* кнопка-бургер — только на мобильных */}
      <button
        type="button"
        aria-label="Open menu"
        onClick={() => setOpen(true)}
        className="md:hidden fixed top-3 right-3 z-50 p-2 rounded-lg bg-surface
                   border border-line shadow-[var(--shadow-pop)] text-ink"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M3 6h18M3 12h18M3 18h18" />
        </svg>
      </button>

      {/* затемнение фона при открытом меню (только мобильные) */}
      {open && (
        <div
          onClick={() => setOpen(false)}
          className="md:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-[2px]"
        />
      )}

      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 w-[230px] shrink-0
                    flex flex-col overflow-hidden
                    bg-surface border-r border-line
                    transition-transform duration-200
                    ${open ? "translate-x-0" : "-translate-x-full"} md:translate-x-0`}
      >
        {/* шапка / логотип */}
        <div className="px-6 py-7 border-b border-line">
          <div className="font-display font-black text-[23px] tracking-[2.5px] uppercase text-ink">
            Hoop<span className="text-brand">Stats</span>
          </div>
          <div className="text-[10px] tracking-[2px] text-faint mt-1">
            NBA ANALYTICS
          </div>
        </div>

        {/* навигация */}
        <nav className="px-3 py-4 flex-1">
          {nav.map((item) => (
            <NavLink
              key={item.id}
              to={item.to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 w-full px-3 py-2.5 rounded-[10px] mb-1
                 text-sm font-medium transition-colors no-underline ${
                   isActive
                     ? "bg-active border border-active-border text-ink"
                     : "border border-transparent text-muted hover:bg-hover hover:text-ink"
                 }`
              }
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth="2"
                   strokeLinecap="round" strokeLinejoin="round">
                <path d={item.icon} />
              </svg>
              {item.label}
            </NavLink>
          ))}

          <div className="h-px bg-line mx-1 my-3" />

          {soon.map((label) => (
            <div
              key={label}
              className="flex items-center justify-between px-3 py-2.5 rounded-[10px] mb-1 text-faint"
            >
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 bg-line rounded-[4px] shrink-0" />
                <span className="text-sm">{label}</span>
              </div>
              <span className="text-[9px] tracking-[1.2px] font-bold px-1.5 py-0.5
                               rounded bg-surface-2 text-faint">
                SOON
              </span>
            </div>
          ))}
        </nav>

        {/* подвал — сезон + переключатель темы */}
        <div className="px-6 py-4 border-t border-line flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="text-[10px] tracking-[1.4px] text-faint font-bold mb-0.5">
              2025–26 SEASON
            </div>
            <div className="text-xs text-muted">Playoffs · Round 1</div>
          </div>
          <ThemeToggle />
        </div>
      </aside>
    </>
  );
}
