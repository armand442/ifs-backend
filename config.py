import os

APP_NAME = "IFS Assistant Backend"
APP_VERSION = "0.2.0"
AI_MODE = "mock"

MONTHLY_LIMIT = int(os.getenv("MONTHLY_MESSAGE_LIMIT_FREE", "120"))
DATABASE_URL = os.getenv("DATABASE_URL")
API_SECRET = os.getenv("API_SECRET")