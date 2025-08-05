"""Settings for the API application."""

import logging
import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings,SettingsConfigDict
from uvicorn.logging import DefaultFormatter

class ConfiguredBaseSettings(BaseSettings):
    """Azure credentials."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )
class Model_Config(BaseSettings):
    """Model configuration settings.

    Attributes:
        model: The model name to use for inference.
        api_key: API key for authentication, required.
        base_url: Base URL for the API endpoint, defaults to environment variable BASE_URL or empty string.
        temperature: Sampling temperature, defaults to 0.7.
        max_tokens: Maximum number of tokens to generate, defaults to 2048.
    """
    api_key: str = os.getenv("API_KEY", "")
    base_url: str = os.getenv("BASE_URL", "http://localhost:11434/v1")
    
class Settings(BaseSettings):
    """Settings for the API application."""

    # General settings
    app_name: str = os.getenv("APP_NAME", "super-agent")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")

    # Logging settings
    log_level: int = int(os.getenv("LOG_LEVEL", logging.INFO))

    # Database settings
    database_url: Optional[str] = os.getenv("DATABASE_URL")

    # API settings
    api_timeout: int = int(os.getenv("API_TIMEOUT", 30))

    # Security settings
    secret_key: Optional[str] = os.getenv("SECRET_KEY")

    # CORS settings
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")

    # model_config
    openai_model_config: Model_Config = Model_Config()

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Create and returns an instance of the Settings class.

    Returns:
        Settings: A new instance of the Settings configuration.
    """
    return Settings()


# Initialize settings
settings = get_settings()

# Configure logging
logging.basicConfig(level=settings.log_level)

# Set the default formatter for all loggers to the uvicorn DefaultFormatter
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    handler.setFormatter(DefaultFormatter(fmt="%(levelprefix)s %(message)s"))

if __name__ == '__main__':
    print(settings.openai_model_config)