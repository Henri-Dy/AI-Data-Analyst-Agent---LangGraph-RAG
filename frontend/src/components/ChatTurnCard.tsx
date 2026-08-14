import type { ChatTurn } from "../hooks/useChat";
import type { ReviewDecision } from "../types";
import { AnswerReport } from "./AnswerReport";
import { HumanReviewPrompt } from "./HumanReviewPrompt";
import { ProgressTrail } from "./ProgressTrail";

export function ChatTurnCard({
  turn,
  onResume,
}: {
  turn: ChatTurn;
  onResume: (id: string, decision: ReviewDecision) => void;
}) {
  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm font-medium text-slate-900">{turn.question}</p>

      <ProgressTrail nodes={turn.progress} active={turn.status === "streaming"} />

      {turn.status === "error" && (
        <p className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{turn.error}</p>
      )}

      {turn.status === "awaiting_review" && turn.interrupt && (
        <HumanReviewPrompt interrupt={turn.interrupt} onSubmit={(decision) => onResume(turn.id, decision)} />
      )}

      {turn.report && <AnswerReport report={turn.report} />}
    </div>
  );
}
