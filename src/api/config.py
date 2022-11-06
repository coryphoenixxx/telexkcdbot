from decouple import config

ADMIN_ID = config("ADMIN_ID", cast=int)
API_PORT = config("API_PORT", default=8080, cast=int)

DATABASE_URL = config("DATABASE_URL", default="postgres://postgres:postgres@db:5432/telexkcdbot")
