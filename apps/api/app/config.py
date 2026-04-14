from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ClaimFlow AI"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "sqlite:///./data/claimflow.db"
    upload_dir: str = "./data/uploads"
    data_dir: str = "./data"
    prompt_version: str = "v1"

    enable_live_llm: bool = False
    llm_provider: str = "openai-compatible"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: int = 45

    auto_approval_ceiling: float = 12000.0
    fraud_escalation_threshold: float = 0.7
    confidence_threshold: float = 0.75
    high_value_threshold_auto: float = 20000.0
    high_value_threshold_healthcare: float = 15000.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    return settings