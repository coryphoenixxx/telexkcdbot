import uvicorn

from .core.config import UvicornConfig, settings


def run_application(config: UvicornConfig):
    uvicorn.run(
        app="src.app:app",
        loop="uvloop",
        host=config.host,
        port=config.port,
        reload=config.reload,
        workers=config.workers,
        lifespan="on",
    )


if __name__ == "__main__":
    run_application(config=settings.uvicorn)
