import os
from pathlib import Path
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Base Directory Paths
BASE_DIR: Path = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _require(key: str) -> str:
    """Retrieve a required environment variable or raise EnvironmentError."""
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing required env variable: {key}")
    return val


OPENAI_API_KEY: str   = _require("OPENAI_API_KEY")
PINECONE_API_KEY: str = _require("PINECONE_API_KEY")

PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "medbot-gale")
PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")

OPENAI_LLM_MODEL: str       = os.getenv("OPENAI_LLM_MODEL", "gpt-4o")
OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSION: int    = int(os.getenv("EMBEDDING_DIMENSION", "1536"))

CHUNK_SIZE: int    = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))

FLASK_ENV: str        = os.getenv("FLASK_ENV", "development")
FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret")
FLASK_PORT: int       = int(os.getenv("PORT", os.getenv("FLASK_PORT", "5000")))
FLASK_DEBUG: bool     = FLASK_ENV == "development"

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR: Path = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

DATA_DIR: Path = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

RETRIEVER_TOP_K: int     = int(os.getenv("RETRIEVER_TOP_K", "5"))
MAX_TOKENS_RESPONSE: int = int(os.getenv("MAX_TOKENS_RESPONSE", "1024"))
LLM_TEMPERATURE: float   = float(os.getenv("LLM_TEMPERATURE", "0.3"))

SUPABASE_URL: str         = _require("SUPABASE_URL")
SUPABASE_SERVICE_KEY: str = _require("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY: str    = os.getenv("SUPABASE_ANON_KEY", "")
JWT_SECRET: str           = _require("JWT_SECRET")
JWT_EXPIRY_HOURS: int     = int(os.getenv("JWT_EXPIRY_HOURS", "24"))