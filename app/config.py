from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://llmref:llmref@localhost:5432/llmref"

    model_config = {"env_file": ".env"}


settings = Settings()
