import ThemeToggle from "../ui/ThemeToggle";
import GlobalSearch from "./GlobalSearch";
export default function TopHeader() {
  return <header className="min-h-[72px] bg-surface border-b border-line px-3 sm:px-6 py-3 flex items-center gap-3 justify-between shrink-0">
    <div className="hidden sm:block font-display font-black text-xl tracking-wide">Hoop<span className="text-brand">Stats</span></div>
    <GlobalSearch/><ThemeToggle/>
  </header>;
}
