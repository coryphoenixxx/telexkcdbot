import os


class Config:
    API_TOKEN = os.getenv("API_TOKEN")
    ADMIN_ID = os.getenv("ADMIN_ID")
    PORT = int(os.getenv("PORT"))
    HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME")
    HEROKU = os.getenv("HEROKU")

