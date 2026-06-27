import { useState } from "react";
import { Toaster } from "sonner";

import { Sidebar } from "@/components/Sidebar";
import Today from "@/pages/Today";
import ExecutiveDashboard from "@/pages/ExecutiveDashboard";
import CommandCenter from "@/pages/CommandCenter";
import Leads from "@/pages/Leads";
import Dashboard from "@/pages/Dashboard";
import Proposals from "@/pages/Proposals";
import Keywords from "@/pages/Keywords";
import Settings from "@/pages/Settings";


const TABS = [
  { id: "today", label: "Today" },
  { id: "executive", label: "Executive" },
  { id: "command-center", label: "Command Center" },
  { id: "proposals", label: "Proposals" },
  { id: "leads", label: "Leads" },
  { id: "operations", label: "Operations" },
  { id: "keywords", label: "Keywords" },
  { id: "settings", label: "Settings" },
];


function renderTab(activeTab) {
  if (activeTab === "executive") {
    return <ExecutiveDashboard />;
  }
  if (activeTab === "command-center") {
    return <CommandCenter />;
  }
  if (activeTab === "proposals") {
    return <Proposals />;
  }
  if (activeTab === "leads") {
    return <Leads />;
  }
  if (activeTab === "operations") {
    return <Dashboard />;
  }
  if (activeTab === "keywords") {
    return <Keywords />;
  }
  if (activeTab === "settings") {
    return <Settings />;
  }
  return <Today />;
}


export default function App() {
  const [activeTab, setActiveTab] = useState("today");

  return (
    <div className="min-h-screen bg-[#050816] text-white">
      <Toaster position="top-right" theme="dark" richColors />
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute left-[-10%] top-[-8%] h-[28rem] w-[28rem] rounded-full bg-cyan-500/12 blur-[140px]" />
        <div className="absolute bottom-[-12%] right-[-8%] h-[32rem] w-[32rem] rounded-full bg-blue-500/10 blur-[160px]" />
      </div>

      <div className="relative z-10 flex min-h-screen">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        <main className="flex-1 px-4 py-5 sm:px-6 lg:px-8 lg:py-8">
          <div className="mx-auto max-w-7xl">
            <div className="mb-6 flex gap-2 overflow-x-auto lg:hidden">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`rounded-2xl px-4 py-2 text-sm font-medium transition ${
                    activeTab === tab.id
                      ? "bg-cyan-400/15 text-cyan-200"
                      : "bg-white/5 text-slate-400"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {renderTab(activeTab)}
          </div>
        </main>
      </div>
    </div>
  );
}
