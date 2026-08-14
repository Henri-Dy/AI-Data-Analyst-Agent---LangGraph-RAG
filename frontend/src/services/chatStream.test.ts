import { describe, expect, it } from "vitest";
import { parseFrame } from "./chatStream";

describe("parseFrame", () => {
  it("parses an update frame", () => {
    const frame = 'event: update\ndata: {"thread_id":"t1","node":"query_analyzer","output":{}}';

    const result = parseFrame(frame);

    expect(result).toEqual({
      event: "update",
      data: { thread_id: "t1", node: "query_analyzer", output: {} },
    });
  });

  it("parses a frame using SSE's \\r\\n line endings", () => {
    const frame = 'event: done\r\ndata: {"thread_id":"t1","report":null}';

    const result = parseFrame(frame);

    expect(result).toEqual({ event: "done", data: { thread_id: "t1", report: null } });
  });

  it("returns null when the event type is missing", () => {
    const frame = 'data: {"thread_id":"t1"}';

    expect(parseFrame(frame)).toBeNull();
  });

  it("returns null when the data line is missing", () => {
    const frame = "event: update";

    expect(parseFrame(frame)).toBeNull();
  });

  it("returns null for a blank frame", () => {
    expect(parseFrame("")).toBeNull();
  });
});
