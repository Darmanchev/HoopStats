import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopHeader from "./TopHeader";

export default function Layout() {
  return (
    <div className="flex flex-col h-dvh overflow-hidden bg-bg">
      <TopHeader />
      <div className="flex flex-col md:flex-row flex-1 min-h-0 overflow-hidden">
        <Sidebar />
        <main className="flex-1 min-w-0 overflow-y-auto relative p-3 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
