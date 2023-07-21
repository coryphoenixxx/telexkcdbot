from aiohttp import web
from src.config import load_config
from src.database.base import SessionFactory
from src.router import router

config = load_config()
app = web.Application()
app.session_factory = SessionFactory.configure(config.db)
router.setup_routes(app)

if __name__ == "__main__":
    web.run_app(app, port=config.api_port)
