"""Centralized limits, paths, and security invariants configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DATA_DIR = BASE_DIR / "nexus_data"
DB_PATH = APP_DATA_DIR / "nexus_history.db"

# Load environment variables securely from project root .env
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

# Ensure data directory exists
os.makedirs(APP_DATA_DIR, exist_ok=True)

# Strict Limits (Invariants)
MAX_COMBINED_INPUT_LENGTH = 100_000  # characters
MAX_GRAPH_NODES = 500
MAX_GRAPH_EDGES = 1_500
MAX_MUTATIONS_PER_RUN = 50
MAX_SEARCH_DEPTH = 10
MAX_TEST_EXECUTION_TIME_SECONDS = 10.0

# HTTP and Inference Network Policy
DEFAULT_LOOPBACK_ENDPOINT = "http://127.0.0.1:8080/v1"
ALLOWED_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
ALLOWED_SCHEMES = {"http", "https"}
OFFICIAL_GEMINI_API_HOST = "generativelanguage.googleapis.com"
DEFAULT_CONNECT_TIMEOUT = 3.0
DEFAULT_READ_TIMEOUT = 30.0

# Safe known GGUF candidates
DEFAULT_MODEL_FILENAME = "google_gemma-4-E2B-it-Q4_0.gguf"
