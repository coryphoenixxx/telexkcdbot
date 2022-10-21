from decouple import config

ADMIN_ID = config("ADMIN_ID", cast=int)


DATABASE_URL = config("DATABASE_URL", default="postgres://postgres:postgres@db:5432/telexkcdbot")
