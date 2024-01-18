import functools
import time

from aiohttp import AsyncResolver, ClientSession, ClientTimeout, TCPConnector
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.app.images.utils import ImageFileSaver, UploadImageReader
from src.core.database import DatabaseHolder, create_engine, create_session_factory
from src.core.settings import get_settings
from .dependency_stubs import (
    ClientSessionDepStub,
    DatabaseHolderDepStub,
    DbEngineDepStub,
    ImageFileSaverDepStub,
    UploadImageReaderDepStub,
)
from .events import lifespan
from .middlewares import ExceptionHandlerMiddleware
from .router import register_routers


def cache(ttl: int):
    def wrapper(func):
        cached_time, session = None, None

        @functools.wraps(func)
        async def wrapped(*args, **kw):
            nonlocal cached_time
            nonlocal session
            now = time.time()
            if not cached_time or now - cached_time > ttl:
                session = await func(*args, **kw)
                cached_time = now
            return session

        return wrapped

    return wrapper


@cache(60)
async def get_client_session(timeout: int = 10):
    connector = TCPConnector(
        resolver=AsyncResolver(nameservers=["8.8.8.8", "8.8.4.4"]),
        ttl_dns_cache=600,
        ssl=False,
    )
    return ClientSession(connector=connector, timeout=ClientTimeout(timeout))


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        lifespan=lifespan,
        debug=settings.app.fastapi.debug,
        docs_url=settings.app.fastapi.docs_url,
        redoc_url=settings.app.fastapi.redoc_url,
        openapi_url=settings.app.fastapi.openapi_url,
        default_response_class=ORJSONResponse,
    )

    register_routers(app)

    app.add_middleware(ExceptionHandlerMiddleware)

    engine = create_engine(settings.db)
    session_factory = create_session_factory(engine)

    app.dependency_overrides.update(
        {
            DbEngineDepStub: lambda: engine,
            DatabaseHolderDepStub: lambda: DatabaseHolder(session_factory=session_factory),
            UploadImageReaderDepStub: lambda: UploadImageReader(
                tmp_dir=settings.app.tmp_dir,
                upload_max_size=eval(settings.app.upload_max_size),
            ),
            ImageFileSaverDepStub: lambda: ImageFileSaver(static_dir=settings.app.static_dir),
            ClientSessionDepStub: get_client_session,
        },
    )

    return app
