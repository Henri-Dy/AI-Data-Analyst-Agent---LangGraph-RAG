"""Runs the compiled LangGraph workflow and streams node-by-node progress
as Server-Sent Events.

The graph's own nodes are synchronous (LLM calls, DB queries), so
`graph.stream()` is a blocking generator. `stream_graph_events()` runs it in
a worker thread and bridges each item back onto the asyncio event loop via
a queue, so a slow LangGraph run never blocks other requests the FastAPI
server is handling concurrently.
"""
import asyncio
import json
from collections.abc import AsyncIterator, Iterator
from functools import lru_cache
from typing import Any

from langgraph.types import Command

from app.graph.graph import build_default_graph

_SENTINEL = object()


@lru_cache
def get_graph():
    """Production graph, built once (real LLM/DB/embedding clients) and
    reused across requests — LangGraph's checkpointer keeps per-thread_id
    conversation state separate, so a single compiled graph instance is
    safe to share."""
    return build_default_graph()


def _graph_updates(graph, run_input: dict | Command, thread_id: str) -> Iterator[dict[str, Any]]:
    """Synchronous generator of SSE-ready event dicts for one graph run
    (either a fresh question or a resume after human review)."""
    config = {"configurable": {"thread_id": thread_id}}

    for step in graph.stream(run_input, config=config, stream_mode="updates"):
        for node_name, node_output in step.items():
            if node_name == "__interrupt__":
                payload = node_output[0].value
                yield {"event": "interrupt", "data": {"thread_id": thread_id, **payload}}
            else:
                yield {"event": "update", "data": {"thread_id": thread_id, "node": node_name, "output": node_output}}

    state = graph.get_state(config)
    if not state.next:
        # The graph ran to completion (as opposed to pausing on an
        # interrupt) — the final report is ready.
        yield {"event": "done", "data": {"thread_id": thread_id, "report": state.values.get("final_report")}}


async def stream_graph_events(graph, run_input: dict | Command, thread_id: str) -> AsyncIterator[dict[str, str]]:
    """Async bridge around `_graph_updates`, formatted for `EventSourceResponse`."""
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def worker() -> None:
        try:
            for event in _graph_updates(graph, run_input, thread_id):
                asyncio.run_coroutine_threadsafe(queue.put(event), loop).result()
        except Exception as e:  # noqa: BLE001 - surfaced to the client as an SSE event, not swallowed
            error_event = {"event": "error", "data": {"thread_id": thread_id, "message": str(e)}}
            asyncio.run_coroutine_threadsafe(queue.put(error_event), loop).result()
        finally:
            asyncio.run_coroutine_threadsafe(queue.put(_SENTINEL), loop).result()

    loop.run_in_executor(None, worker)

    while True:
        event = await queue.get()
        if event is _SENTINEL:
            break
        yield {"event": event["event"], "data": json.dumps(event["data"], default=str)}
