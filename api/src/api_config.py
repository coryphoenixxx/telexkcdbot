from decouple import config

ADMIN_ID = config("ADMIN_ID", cast=int)

API_PORT = config("API_PORT", default=8080, cast=int)

DB_USER = config('DB_USER', default='postgres')
DB_PASS = config('DB_PASS', default='postgres')
DB_PORT = config('DB_PORT', default='5432')
DB_HOST = config('DB_HOST', default='db')
DB_NAME = config('DB_NAME', default='postgres')


DATABASE_URL = config(
    "DATABASE_URL",
    default=f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
