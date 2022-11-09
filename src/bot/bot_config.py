from pathlib import Path

from decouple import config

API_TOKEN = config("API_TOKEN")
ADMIN_ID = config("ADMIN_ID", cast=int)

I18N_DOMAIN = "telexkcdbot"

DOMAIN_NAME = config("DOMAIN_NAME")
WEBHOOK_PATH = f"/bot/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{DOMAIN_NAME}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
BOT_PORT = config("BOT_PORT", default=5050, cast=int)
API_PORT = config("API_PORT", default=8080, cast=int)

BASE_DIR = Path(__file__).parent
IMG_DIR = BASE_DIR / "static/img"
RU_COMIC_DATA_DIR = BASE_DIR / "static/ru_comics_data"
LOCALES_DIR = BASE_DIR / "locales"

CHUNK_SIZE = config("CHUNK_SIZE", default=20, cast=int)
