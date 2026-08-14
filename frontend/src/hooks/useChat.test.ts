import { describe, expect, it } from "vitest";
import { applyEvent } from "./useChat";
import type { ChatTurn } from "./useChat";

function baseTurn(overrides: Partial<ChatTurn> = {}): ChatTurn {
  return {
    id: "turn-1",
    question: "What is revenue?",
    status: "streaming",
    progress: [],
    interrupt: null,
    report: null,
    error: null,
    ...overrides,
  };
}

describe("applyEvent", () => {
  it("appends the node name on an update event", () => {
    const turn = baseTurn({ progress: ["query_analyzer"] });

    const next = applyEvent(turn, {
      event: "update",
      data: { thread_id: "turn-1", node: "schema_agent", output: {} },
    });

    expect(next.progress).toEqual(["query_analyzer", "schema_agent"]);
    expect(next.status).toBe("streaming");
  });

  it("moves to awaiting_review and stores the interrupt payload on an interrupt event", () => {
    const turn = baseTurn();
    const interruptData = {
      thread_id: "turn-1",
      reason: "confidence_below_threshold",
      confidence: 0.2,
      narrative: "Draft answer.",
      fact_check_notes: ["UNVERIFIED: ..."],
    };

    const next = applyEvent(turn, { event: "interrupt", data: interruptData });

    expect(next.status).toBe("awaiting_review");
    expect(next.interrupt).toEqual(interruptData);
  });

  it("moves to done, clears any interrupt, and stores the report on a done event", () => {
    const turn = baseTurn({ status: "awaiting_review", interrupt: { thread_id: "turn-1", reason: "x", confidence: 0.2, narrative: "x", fact_check_notes: [] } });
    const report = { answer: "Revenue is 100.", confidence: 1, sql: null, sql_row_count: null, chart: null, fact_check_notes: [], human_reviewed: true, sources: [], errors: [] };

    const next = applyEvent(turn, { event: "done", data: { thread_id: "turn-1", report } });

    expect(next.status).toBe("done");
    expect(next.interrupt).toBeNull();
    expect(next.report).toEqual(report);
  });

  it("moves to error and stores the message on an error event", () => {
    const turn = baseTurn();

    const next = applyEvent(turn, { event: "error", data: { thread_id: "turn-1", message: "boom" } });

    expect(next.status).toBe("error");
    expect(next.error).toBe("boom");
  });
});
