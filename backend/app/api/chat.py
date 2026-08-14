"""Chat endpoint: runs the LangGraph workflow and streams node-by-node
progress as Server-Sent Events, including a pause for human review when
the Fact Checker's confidence is low.
"""
import uuid

from fastapi import APIRouter, Depends
from langgraph.types import Command
from sse_starlette.sse import EventSourceResponse

from app.models.chat import ChatRequest, ChatResumeRequest
from app.services.chat_service import get_graph, stream_graph_events

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest, graph=Depends(get_graph)) -> EventSourceResponse:
    """Starts (or continues, via `thread_id`) a conversation. Streams
    `update` events as each graph node finishes, an `interrupt` event if
    the answer needs human review, or a `done` event with the final report.
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    events = stream_graph_events(graph, {"question": request.question}, thread_id)
    return EventSourceResponse(events)


@router.post("/resume")
async def resume(request: ChatResumeRequest, graph=Depends(get_graph)) -> EventSourceResponse:
    """Resumes a conversation paused on human review (see the `interrupt`
    event from `POST /api/chat`) with the reviewer's decision."""
    decision = {
        "approved": request.approved,
        "reviewer_notes": request.reviewer_notes,
        "edited_narrative": request.edited_narrative,
    }
    events = stream_graph_events(graph, Command(resume=decision), request.thread_id)
    return EventSourceResponse(events)
