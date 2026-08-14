import { ChatComposer } from "../components/ChatComposer";
import { ChatTurnCard } from "../components/ChatTurnCard";
import { useChat } from "../hooks/useChat";

export function ChatPage() {
  const { turns, ask, resume } = useChat();
  const isStreaming = turns.some((turn) => turn.status === "streaming");

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {turns.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">
            Ask a question about your data to get started.
          </div>
        ) : (
          turns.map((turn) => <ChatTurnCard key={turn.id} turn={turn} onResume={resume} />)
        )}
      </div>

      <div className="border-t border-slate-200 bg-white p-4">
        <ChatComposer onSubmit={ask} disabled={isStreaming} />
      </div>
    </div>
  );
}
