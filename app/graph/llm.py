from langchain_openai import ChatOpenAI

from app.config import get_settings

CLAUDE_KEY_PREFIX = "sk-ant-"


def is_claude_key(api_key: str | None) -> bool:
    return bool(api_key) and api_key.strip().startswith(CLAUDE_KEY_PREFIX)


def get_llm_for_tenant(api_key: str):
    """
    Build the chat model scoped to one tenant's own AI key: OpenAI, or Claude (Anthropic) when the key
    starts with "sk-ant-". Both are LangChain chat models, so the rest of the graph does not care which one it gets.
    Not cached — each request may belong to a different tenant, and the
    key can change at any time via the tenant's Company Profile settings.
    (Embeddings are separate: they use Botivate's own OpenAI key, see retrieval/embeddings.py.)
    """
    settings = get_settings()
    if is_claude_key(api_key):
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.claude_chat_model,
            api_key=api_key.strip(),
            # no temperature: current Claude models reject it (HTTP 400 "`temperature` is deprecated for this model")
            streaming=True,
            max_tokens=1024,
        )
    return ChatOpenAI(
        model=settings.openai_chat_model,
        api_key=api_key,
        temperature=0.2,
        streaming=True,
    )
