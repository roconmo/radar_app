from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-6"
    similarity_threshold: float = 0.85  # para deduplicación fuzzy
    history_db_path: str = "data/history.db"
    url_retention_days: int = 30  # URLs vistas hace más de N días se tratan como nuevas

    class Config:
        env_file = ".env"


settings = Settings()
