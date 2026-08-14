import { ChatPage } from "./pages/ChatPage";

function App() {
  return (
    <div className="flex h-screen flex-col bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white px-6 py-3">
        <h1 className="text-lg font-semibold tracking-tight">AI Data Analyst</h1>
      </header>

      <ChatPage />
    </div>
  );
}

export default App;
