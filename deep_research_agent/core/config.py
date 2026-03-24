"""Configuration management for Deep Research Agent."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class SearchDepth(str, Enum):
    """Search depth levels."""

    SHALLOW = "shallow"
    NORMAL = "normal"
    DEEP = "deep"


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    # API Keys
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    serpapi_api_key: Optional[str] = None
    langchain_api_key: Optional[str] = None

    # LangSmith
    langchain_project: str = "deep-research-agent"
    langchain_tracing_v2: bool = False

    # Model Configuration
    model_tier_light: str = "gpt-4o-mini"
    model_tier_medium: str = "gpt-4o"
    model_tier_strong: str = "o1-preview"

    # Fallback Models
    model_fallback_light: str = "claude-3-haiku-20240307"
    model_fallback_medium: str = "claude-3-sonnet-20241022"
    model_fallback_strong: str = "claude-3-opus-20240229"

    # Research Configuration
    max_iterations: int = 3
    search_results_per_query: int = 5
    search_depth: SearchDepth = SearchDepth.NORMAL
    requests_per_minute: int = 60

    # Storage Configuration
    chroma_persist_dir: str = "./data/chroma"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    output_dir: str = "./output"

    # Logging
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"

    def __post_init__(self):
        """Load from environment variables."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", self.openai_base_url)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
        self.serpapi_api_key = os.getenv("SERPAPI_API_KEY", self.serpapi_api_key)
        self.langchain_api_key = os.getenv("LANGCHAIN_API_KEY", self.langchain_api_key)

        self.langchain_project = os.getenv("LANGCHAIN_PROJECT", self.langchain_project)
        self.langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

        self.model_tier_light = os.getenv("MODEL_TIER_LIGHT", self.model_tier_light)
        self.model_tier_medium = os.getenv("MODEL_TIER_MEDIUM", self.model_tier_medium)
        self.model_tier_strong = os.getenv("MODEL_TIER_STRONG", self.model_tier_strong)

        self.max_iterations = int(os.getenv("MAX_ITERATIONS", self.max_iterations))
        self.search_results_per_query = int(
            os.getenv("SEARCH_RESULTS_PER_QUERY", self.search_results_per_query)
        )
        self.search_depth = SearchDepth(os.getenv("SEARCH_DEPTH", self.search_depth.value))
        self.requests_per_minute = int(os.getenv("REQUESTS_PER_MINUTE", self.requests_per_minute))

        self.chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", self.chroma_persist_dir)
        self.embedding_model = os.getenv("EMBEDDING_MODEL", self.embedding_model)
        self.output_dir = os.getenv("OUTPUT_DIR", self.output_dir)

        self.log_level = LogLevel(os.getenv("LOG_LEVEL", self.log_level.value))
        self.log_format = os.getenv("LOG_FORMAT", self.log_format)

    def validate(self) -> list[str]:
        """Validate settings and return list of missing required keys."""
        missing = []
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
        return missing


# Global settings instance
settings = Settings()
