# services/backend/app/config.py
"""
Configuration loader for ChangeAnyFile API backend.

This module:
- Loads .env (if present) using python-dotenv
- Provides BASE_DIR, UPLOAD_DIR, PROCESSED_DIR as absolute paths
- Interprets relative paths as relative to backend BASE_DIR
- Provides CORS_ORIGINS as a list
- Provides defaults for development
"""

from pathlib import Path
import os

# ----------------------------------------------------
# Load .env if python-dotenv is installed
# ----------------------------------------------------
try:
    from dotenv import load_dotenv

    # Path: services/backend/.env
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except Exception:
    # Safe fallback: no .env loaded
    pass

# ----------------------------------------------------
# Base backend directory
# Example: C:/project/changeanyfile/services/backend
# ----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ----------------------------------------------------
# Helper: Get env with fallback
# ----------------------------------------------------
def _get_env(name: str, default=None):
    return os.environ.get(name, default)


# ----------------------------------------------------
# Helper: Resolve path safely
# ----------------------------------------------------
def _resolve_path(value: str, base: Path) -> Path:
    """
    Resolve a path string into an absolute Path:

    Cases:
    - If path is absolute → return as-is resolved
    - If path is relative → treat it as relative to backend BASE_DIR
    - If value is None → return None
    """
    if value is None:
        return None

    p = Path(value)

    # Case 1: absolute path (Windows: C:\..., Linux: /...)
    if p.is_absolute():
        return p.resolve()

    # Case 2: treat as relative to backend BASE_DIR
    return (base / p).resolve()


# ----------------------------------------------------
# Upload & Processed directories
# ----------------------------------------------------
# Raw values from env (could be absolute or relative)
_raw_upload = _get_env("UPLOAD_DIR", None)
_raw_processed = _get_env("PROCESSED_DIR", None)

# Default: BASE_DIR/uploads or BASE_DIR/processed
UPLOAD_DIR = _resolve_path(_raw_upload, BASE_DIR) if _raw_upload else (BASE_DIR / "uploads").resolve()
PROCESSED_DIR = _resolve_path(_raw_processed, BASE_DIR) if _raw_processed else (BASE_DIR / "processed").resolve()

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------
# CORS origins (comma-separated in env)
# Example: CORS_ORIGINS="http://localhost:3000,https://myapp.com"
# ----------------------------------------------------
_cors_raw = _get_env("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS = [origin.strip() for origin in _cors_raw.split(",") if origin.strip()]


# ----------------------------------------------------
# Additional optional config (for future sprint)
# ----------------------------------------------------
ENV = _get_env("ENV", "development")
PORT = int(_get_env("PORT", 8000))

DATABASE_URL = _get_env("DATABASE_URL", None)
S3_BUCKET = _get_env("S3_BUCKET", None)

