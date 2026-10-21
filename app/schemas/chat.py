from typing import Literal

from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_history: list[ConversationTurn] = Field(default_factory=list, max_length=20)


class SourceRef(BaseModel):
    module: str
    doc_title: str
    source_path: str


class ChatResponse(BaseModel):
    answer: str
    in_scope: bool
    module_context: str | None = None
    sources: list[SourceRef] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    vector_store_backend: str | None = None
