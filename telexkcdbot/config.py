from os import getenv
from pathlib import Path


API_TOKEN = getenv('API_TOKEN')
ADMIN_ID = int(getenv('ADMIN_ID'))

I18N_DOMAIN = 'telexkcdbot'

DATABASE_URL = getenv('DATABASE_URL')

HEROKU = bool(getenv('HEROKU'))

HEROKU_APP_NAME = getenv('HEROKU_APP_NAME')
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
WEBAPP_HOST = '0.0.0.0'
PORT = int(getenv('PORT'))

BASE_DIR = Path(__file__).parent.parent
IMG_DIR = BASE_DIR / 'static/img'
LOCALES_DIR = BASE_DIR / 'locales'
LOGS_DIR = BASE_DIR / 'logs'
