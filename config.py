import os

APP_NAME = "IFS Assistant Backend"
APP_VERSION = "0.3.0"
AI_MODE = "mock"

MONTHLY_LIMIT = int(os.getenv("MONTHLY_MESSAGE_LIMIT_FREE", "120"))
DATABASE_URL = os.getenv("DATABASE_URL")
API_SECRET = os.getenv("API_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_ENABLED = os.getenv("AI_ENABLED", "false").lower() == "true"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")