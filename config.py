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

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "7200"))
    JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "False").lower() == "true"