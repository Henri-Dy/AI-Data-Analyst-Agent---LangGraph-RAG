import { useState } from "react";
import { ChatPage } from "./pages/ChatPage";
import { DataSourcesPage } from "./pages/DataSourcesPage";

type Tab = "chat" | "data-sources";

function App() {
  const [tab, setTab] = useState<Tab>("chat");

  return (
    <div className="flex h-screen flex-col bg-slate-50 text-slate-900">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <h1 className="text-lg font-semibold tracking-tight">AI Data Analyst</h1>
        <nav className="flex gap-1">
          <button
            type="button"
            onClick={() => setTab("chat")}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${
              tab === "chat" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            Chat
          </button>
          <button
            type="button"
            onClick={() => setTab("data-sources")}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${
              tab === "data-sources" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            Data Sources
          </button>
        </nav>
      </header>

      {tab === "chat" ? <ChatPage /> : <DataSourcesPage />}
    </div>
  );
}

export default App;
