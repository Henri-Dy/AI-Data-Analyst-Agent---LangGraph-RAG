import { useState } from "react";
import type { ChatInterruptEvent, ReviewDecision } from "../types";
import { ConfidenceBadge } from "./ConfidenceBadge";

export function HumanReviewPrompt({
  interrupt,
  onSubmit,
}: {
  interrupt: ChatInterruptEvent;
  onSubmit: (decision: ReviewDecision) => void;
}) {
  const [narrative, setNarrative] = useState(interrupt.narrative);
  const [notes, setNotes] = useState("");

  return (
    <div className="space-y-3 rounded-lg border border-amber-300 bg-amber-50 p-3">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-amber-700">Needs human review</span>
        <ConfidenceBadge confidence={interrupt.confidence} />
      </div>

      {interrupt.fact_check_notes.length > 0 && (
        <ul className="space-y-1 text-xs text-amber-800">
          {interrupt.fact_check_notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      )}

      <textarea
        value={narrative}
        onChange={(e) => setNarrative(e.target.value)}
        rows={3}
        className="w-full rounded-md border border-amber-300 bg-white p-2 text-sm outline-none focus:border-amber-500"
      />

      <input
        type="text"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Reviewer notes (optional)"
        className="w-full rounded-md border border-amber-300 bg-white p-2 text-sm outline-none focus:border-amber-500"
      />

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onSubmit({ approved: true, reviewer_notes: notes || null, edited_narrative: narrative })}
          className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
        >
          Approve
        </button>
        <button
          type="button"
          onClick={() => onSubmit({ approved: false, reviewer_notes: notes || null, edited_narrative: narrative })}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
