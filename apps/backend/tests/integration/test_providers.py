import sqlalchemy
from dishka import Provider, Scope, provide

from backend.infrastructure.broker.config import NatsConfig
from backend.infrastructure.database.config import DbConfig


class TestDbConfigProvider(Provider):
    __test__ = False

    def __init__(self, postgres_url: str) -> None:
        self._postgres_url = postgres_url
        super().__init__()

    @provide(scope=Scope.APP)
    def provide_test_db_config(self) -> DbConfig:
        url = sqlalchemy.make_url(self._postgres_url)

        return DbConfig(
            host=url.host,
            port=url.port,
            user=url.username,
            password=url.password,
            dbname=url.database,
            echo=False,
            pool_size=5,
        )


class TestNatsConfigProvider(Provider):
    __test__ = False

    def __init__(self, nats_uri: str) -> None:
        self._nats_uri = nats_uri
        super().__init__()

    @provide(scope=Scope.APP)
    def provide_test_nats_config(self) -> NatsConfig:
        return NatsConfig(url=self._nats_uri)
