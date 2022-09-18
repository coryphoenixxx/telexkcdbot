from pathlib import Path

from decouple import config

API_TOKEN = config("API_TOKEN")
ADMIN_ID = config("ADMIN_ID", cast=int)

I18N_DOMAIN = "telexkcdbot"

DEV = config("DEV", default=False, cast=bool)

DATABASE_URL = config("DATABASE_URL", default="postgres://postgres:postgres@localhost:5432/telexkcdbot")

HOST_IP_ADDR = config("HOST_IP_ADDR", default="localhost")
WEBHOOK_PATH = f"/bot/webhook/{API_TOKEN}"
WEBHOOK_URL = f"https://{HOST_IP_ADDR}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
PORT = config("PORT", default=5050, cast=int)

BASE_DIR = Path(__file__).parent.parent
IMG_DIR = BASE_DIR / "static/img"
LOCALES_DIR = BASE_DIR / "locales"
LOGS_DIR = BASE_DIR / "logs"
