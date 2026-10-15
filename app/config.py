from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # Used when a company's key is a Claude (Anthropic) key (starts with "sk-ant-"). Small and fast, like gpt-4o-mini.
    claude_chat_model: str = "claude-haiku-5-5"

    jwt_secret: str = "your-secret-key"

    node_backend_url: str = "http://localhost:5000/api"

    database_url: str = ""

    vector_store_backend: str = "chroma"
    chroma_persist_dir: str = "./data/chroma"

    knowledge_base_dir: str = "./knowledge_base"
    department_module_map_path: str = "./config/department_module_map.yaml"

    app_env: str = "development"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
