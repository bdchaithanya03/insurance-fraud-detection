import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "local-development-key")
    USE_MEMORY_DB = os.getenv("USE_MEMORY_DB", "0") == "1"
    MYSQL_CONFIG = {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.getenv("MYSQL_DATABASE", "insurance_fraud"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
    }
    GANACHE_RPC_URL = os.getenv("GANACHE_RPC_URL", "http://127.0.0.1:7545")
    CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")
    MODEL_PATH = BASE_DIR / "ml" / "model.pkl"
    MODEL_METADATA_PATH = BASE_DIR / "ml" / "model_metadata.json"
    CONTRACT_ARTIFACT_PATH = BASE_DIR / "blockchain" / "build" / "contracts" / "GenuineClaims.json"
