import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = (BASE_DIR / "base.db").as_posix()


class Config:
    STRIPE_SECRET_KEY = os.environ["STRIPE_SECRET_KEY"]
    SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False