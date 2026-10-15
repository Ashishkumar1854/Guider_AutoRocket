import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_bearer_token
from app.core.exceptions import AuthError
from app.graph import compiled as compiled_module
from app.schemas.chat import ChatRequest, ChatResponse, SourceRef

router = APIRouter()
logger = logging.getLogger("autorocket_ai_assistant.chat")


def _error_frame(code: str, message: str) -> str:
    """One SSE error frame. `code` is machine-readable; `message` is safe to show a user."""
    return f"data: {json.dumps({'type': 'error', 'code': code, 'message': message})}\n\n"


def _classify_failure(exc: Exception) -> tuple[str, str]:
    """Map an unexpected exception to a (code, user-safe message). The raw text stays in the log."""
    name = type(exc).__name__
    text = str(exc).lower()
    # An account with no credit left (OpenAI 429 "insufficient_quota", Claude "credit balance is too low"):
    # waiting does not help, so it must not be reported as "busy".
    if "insufficient_quota" in text or "credit balance" in text or "credit_balance" in text:
        return "no_credits", "The AI account for your company has no credits left. Please contact your admin."
    if name == "RateLimitError" or "rate limit" in text or "429" in text:
        return "busy", "The assistant is busy right now. Please try again in a minute."
    if (
        name == "AuthenticationError"
        or "incorrect api key" in text
        or "invalid_api_key" in text
        or "invalid x-api-key" in text
    ):
        return "no_key", "The AI key for your company is not valid. Please contact your admin."
    return "unavailable", "The assistant is not available right now. Please try again later."


def _auth_failure(message: str) -> tuple[str, str]:
    """Auth/tenant-key failures raised inside the graph, as (code, message)."""
    if "openai key" in message.lower():
        return "no_key", "The assistant is not set up for your company yet. Please contact your admin."
    return "not_authenticated", "Your session has expired. Please log in again."


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, bearer_token: str = Depends(get_bearer_token)) -> ChatResponse:
    graph = compiled_module.get_compiled_graph()

    result = await graph.ainvoke(
        {
            "bearer_token": bearer_token,
            "user_message": request.message,
            "conversation_history": request.conversation_history,
        }
    )

    if result.get("auth_error"):
        raise AuthError(result["auth_error"])

    sources: list[SourceRef] = result.get("sources", [])
    return ChatResponse(
        answer=result["answer"],
        in_scope=result.get("in_scope", True),
        module_context=result.get("requested_module_hint"),
        sources=sources,
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, bearer_token: str = Depends(get_bearer_token)):
    """
    SSE version of /chat. The LangGraph flow still resolves the full answer
    in one shot (retrieval + generation aren't token-streamed internally),
    but the response is emitted to the client as incremental "delta" frames
    so the widget can render it progressively instead of waiting for the
    entire answer at once.

    Frame shapes (each is one `data: {...}\\n\\n` line):
      {"type": "delta", "content": "..."}      — one chunk of answer text
      {"type": "sources", "sources": [...]}    — SourceRef list, sent once at the end
      {"type": "error", "message": "..."}      — auth or upstream failure
      {"type": "done"}                          — stream finished
    """

    async def event_generator():
        graph = compiled_module.get_compiled_graph()

        try:
            result = await graph.ainvoke(
                {
                    "bearer_token": bearer_token,
                    "user_message": request.message,
                    "conversation_history": request.conversation_history,
                }
            )
        except Exception as exc:  # defensive: never let the stream die silently
            logger.exception("chat stream failed")  # full detail only in the server log
            code, message = _classify_failure(exc)
            yield _error_frame(code, message)
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        if result.get("auth_error"):
            code, message = _auth_failure(result["auth_error"])
            yield _error_frame(code, message)
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        answer = result.get("answer", "")
        sources: list[SourceRef] = result.get("sources", [])

        words = answer.split(" ")
        chunk_size = 3
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size])
            if i + chunk_size < len(words):
                chunk += " "
            yield f"data: {json.dumps({'type': 'delta', 'content': chunk})}\n\n"

        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'sources': [s.model_dump() for s in sources]})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
