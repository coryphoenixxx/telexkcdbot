import os


class Config:
    API_TOKEN = os.getenv("API_TOKEN")
    ADMIN_ID = os.getenv("ADMIN_ID")
