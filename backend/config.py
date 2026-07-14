"""
config.py
---------
Centralized configuration for the AI Document Assistant backend.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


class Config:
    """Application configuration loaded from backend/.env."""

    # Paths
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    VECTORSTORE_DIR = BASE_DIR / "vectorstore"
    DATABASE_PATH = BASE_DIR / "app_data.db"

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    # API keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

    # LLM provider
    LLM_PROVIDER = os.getenv(
        "LLM_PROVIDER",
        "groq",
    ).strip().lower()

    # Models
    GROQ_MODEL_NAME = os.getenv(
        "GROQ_MODEL_NAME",
        "openai/gpt-oss-20b",
    ).strip()

    OPENAI_MODEL_NAME = os.getenv(
        "OPENAI_MODEL_NAME",
        "gpt-4o-mini",
    ).strip()

    OLLAMA_MODEL_NAME = os.getenv(
        "OLLAMA_MODEL_NAME",
        "llama3.2",
    ).strip()

    LLM_TEMPERATURE = float(
        os.getenv("LLM_TEMPERATURE", "0.2")
    )

    # Embeddings
    EMBEDDING_MODEL_NAME = os.getenv(
        "EMBEDDING_MODEL_NAME",
        "sentence-transformers/all-MiniLM-L6-v2",
    ).strip()

    # Chunking
    CHUNK_SIZE = int(
        os.getenv("CHUNK_SIZE", "1000")
    )

    CHUNK_OVERLAP = int(
        os.getenv("CHUNK_OVERLAP", "150")
    )

    # Retrieval
    RETRIEVAL_TOP_K = int(
        os.getenv("RETRIEVAL_TOP_K", "4")
    )

    # FAISS
    FAISS_INDEX_NAME = "faiss_index"

    # CORS
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]

    @classmethod
    def validate(cls) -> None:
        """Validate configuration before starting the application."""

        supported_providers = {
            "groq",
            "openai",
            "ollama",
        }

        if cls.LLM_PROVIDER not in supported_providers:
            raise ValueError(
                f"Unsupported LLM_PROVIDER '{cls.LLM_PROVIDER}'. "
                "Use 'groq', 'openai', or 'ollama'."
            )

        if cls.LLM_PROVIDER == "groq" and not cls.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is missing in backend/.env."
            )

        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is missing in backend/.env."
            )

        if cls.CHUNK_SIZE <= 0:
            raise ValueError(
                "CHUNK_SIZE must be greater than 0."
            )

        if cls.CHUNK_OVERLAP < 0:
            raise ValueError(
                "CHUNK_OVERLAP cannot be negative."
            )

        if cls.CHUNK_OVERLAP >= cls.CHUNK_SIZE:
            raise ValueError(
                "CHUNK_OVERLAP must be smaller than CHUNK_SIZE."
            )

        if cls.RETRIEVAL_TOP_K <= 0:
            raise ValueError(
                "RETRIEVAL_TOP_K must be greater than 0."
            )