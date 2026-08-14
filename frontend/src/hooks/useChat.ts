import { useCallback, useState } from "react";
import { streamChatQuestion, streamChatResume } from "../services/chatStream";
import type { ChatEvent, ChatInterruptEvent, FinalReport, ReviewDecision } from "../types";

export type ChatTurnStatus = "streaming" | "awaiting_review" | "done" | "error";

export interface ChatTurn {
  id: string;
  question: string;
  status: ChatTurnStatus;
  progress: string[];
  interrupt: ChatInterruptEvent | null;
  report: FinalReport | null;
  error: string | null;
}

function applyEvent(turn: ChatTurn, event: ChatEvent): ChatTurn {
  switch (event.event) {
    case "update":
      return { ...turn, progress: [...turn.progress, event.data.node] };
    case "interrupt":
      return { ...turn, status: "awaiting_review", interrupt: event.data };
    case "done":
      return { ...turn, status: "done", interrupt: null, report: event.data.report };
    case "error":
      return { ...turn, status: "error", error: event.data.message };
  }
}

export function useChat() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);

  const updateTurn = useCallback((id: string, updater: (turn: ChatTurn) => ChatTurn) => {
    setTurns((prev) => prev.map((turn) => (turn.id === id ? updater(turn) : turn)));
  }, []);

  const ask = useCallback(
    (question: string) => {
      const id = crypto.randomUUID();
      setTurns((prev) => [
        ...prev,
        { id, question, status: "streaming", progress: [], interrupt: null, report: null, error: null },
      ]);

      streamChatQuestion(question, id, (event) => updateTurn(id, (turn) => applyEvent(turn, event))).catch(
        (err: unknown) => {
          updateTurn(id, (turn) => ({ ...turn, status: "error", error: String(err) }));
        },
      );
    },
    [updateTurn],
  );

  const resume = useCallback(
    (id: string, decision: ReviewDecision) => {
      updateTurn(id, (turn) => ({ ...turn, status: "streaming" }));

      streamChatResume(id, decision, (event) => updateTurn(id, (turn) => applyEvent(turn, event))).catch(
        (err: unknown) => {
          updateTurn(id, (turn) => ({ ...turn, status: "error", error: String(err) }));
        },
      );
    },
    [updateTurn],
  );

  return { turns, ask, resume };
}
