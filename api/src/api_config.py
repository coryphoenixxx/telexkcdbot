from decouple import config

ADMIN_ID = config("ADMIN_ID", cast=int)

API_PORT = config("API_PORT", default=8080, cast=int)

POSTGRES_USER = config('POSTGRES_USER', default="postgres")
POSTGRES_PASSWORD = config('POSTGRES_PASSWORD', default="postgres")
POSTGRES_PORT = config('DB_PORT', default=5432, cast=int)
POSTGRES_DB = config('POSTGRES_DB', default="telexkcdbot")

DATABASE_URL = config(
    "DATABASE_URL",
    default=f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:{POSTGRES_PORT}/{POSTGRES_DB}"
)
