"""Request schemas for the chat API."""
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    thread_id: str | None = None


class ChatResumeRequest(BaseModel):
    thread_id: str
    approved: bool
    reviewer_notes: str | None = None
    edited_narrative: str | None = None
