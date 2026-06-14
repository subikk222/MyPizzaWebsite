import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    STRIPE_SECRET_KEY = os.environ["STRIPE_SECRET_KEY"]
    SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    DATABASE = "base.db"