import os


API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
DATABASE_URL = os.getenv('DATABASE_URL')
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
HEROKU = os.getenv('HEROKU')
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
PORT = int(os.getenv('PORT'))
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
WEBAPP_HOST = '0.0.0.0'
