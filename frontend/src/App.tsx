function App() {
  return (
    <div className="flex h-screen flex-col bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white px-6 py-3">
        <h1 className="text-lg font-semibold tracking-tight">AI Data Analyst</h1>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-64 shrink-0 border-r border-slate-200 bg-white p-4">
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Datasets
          </h2>
          <p className="text-sm text-slate-400">No dataset uploaded yet.</p>
        </aside>

        <main className="flex flex-1 flex-col overflow-y-auto p-6">
          <div className="flex flex-1 items-center justify-center text-sm text-slate-400">
            Ask a question about your data to get started.
          </div>
        </main>
      </div>

      <footer className="border-t border-slate-200 bg-white p-4">
        <input
          type="text"
          placeholder="Ask a question..."
          className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm outline-none focus:border-slate-500"
          disabled
        />
      </footer>
    </div>
  );
}

export default App;
