import type { ChatEvent } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

/**
 * POSTs to an SSE endpoint and invokes `onEvent` for every `event:`/`data:`
 * frame as it arrives. Axios doesn't expose a streaming body reader in the
 * browser, so this uses `fetch` directly — the backend's chat endpoints
 * are the only streaming responses in this app.
 */
async function streamSSE(
  path: string,
  body: unknown,
  onEvent: (event: ChatEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Request to ${path} failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split(/\r?\n\r?\n/);
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const parsed = parseFrame(frame);
      if (parsed) onEvent(parsed);
    }
  }
}

export function parseFrame(frame: string): ChatEvent | null {
  let eventType: string | null = null;
  let data: string | null = null;

  for (const line of frame.split(/\r?\n/)) {
    if (line.startsWith("event:")) eventType = line.slice("event:".length).trim();
    else if (line.startsWith("data:")) data = line.slice("data:".length).trim();
  }

  if (!eventType || data === null) return null;
  return { event: eventType, data: JSON.parse(data) } as ChatEvent;
}

export function streamChatQuestion(
  question: string,
  threadId: string | null,
  onEvent: (event: ChatEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  return streamSSE("/api/chat", { question, thread_id: threadId }, onEvent, signal);
}

export function streamChatResume(
  threadId: string,
  decision: { approved: boolean; reviewer_notes: string | null; edited_narrative: string | null },
  onEvent: (event: ChatEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  return streamSSE(
    "/api/chat/resume",
    { thread_id: threadId, ...decision },
    onEvent,
    signal,
  );
}
