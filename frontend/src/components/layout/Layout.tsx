import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopHeader from "./TopHeader";

export default function Layout() {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-bg">
      <TopHeader />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto relative p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
