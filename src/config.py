from pathlib import Path

from decouple import config

API_TOKEN = config("API_TOKEN")
ADMIN_ID = config("ADMIN_ID", cast=int)

I18N_DOMAIN = "telexkcdbot"

DATABASE_URL = config("DATABASE_URL", default="postgres://postgres:postgres@localhost:5432/telexkcdbot")

DOMAIN_NAME = config("DOMAIN_NAME")
WEBHOOK_PATH = f"/bot/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{DOMAIN_NAME}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
PORT = config("PORT", default=5050, cast=int)

BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
IMG_DIR = BASE_DIR / "src/bot/static/img"
RU_COMIC_DATA_DIR = BASE_DIR / "src/bot/static/ru_comics_data"
LOCALES_DIR = BASE_DIR / "src/bot/locales"
