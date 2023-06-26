from pathlib import Path

from decouple import config

TG_API_TOKEN = config("API_TOKEN")
ADMIN_ID = config("ADMIN_ID", cast=int)

I18N_DOMAIN = "telexkcdbot"

DOMAIN_NAME = config("DOMAIN_NAME")
WEBHOOK_PATH = f"/bot/webhook/{TG_API_TOKEN}"
WEBHOOK_URL = f"{DOMAIN_NAME}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
BOT_PORT = config("BOT_PORT", default=5050, cast=int)

API_PORT = config("API_PORT", default=8080, cast=int)
API_URL = config("API_URL", default=f"http://localhost:{API_PORT}", cast=str)

BASE_DIR = Path(__file__).parent
IMG_DIR = BASE_DIR / "static/img"
RU_COMICS_DATA_DIR = BASE_DIR / "static/ru_comics_data"
RU_COMICS_IMAGES = RU_COMICS_DATA_DIR / "images"
RU_COMICS_CSV = RU_COMICS_DATA_DIR / "data.csv"
LOCALES_DIR = BASE_DIR / "locales"

CHUNK_SIZE = config("CHUNK_SIZE", default=20, cast=int)
