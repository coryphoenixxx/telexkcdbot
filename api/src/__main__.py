import uvicorn

from .core.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        app="src.app:create_app",
        factory=True,
        loop="uvloop",
        http="httptools",
        host=settings.uvicorn.host,
        port=settings.uvicorn.port,
        reload=settings.uvicorn.reload,
        workers=settings.uvicorn.workers,
        lifespan="on",
    )
