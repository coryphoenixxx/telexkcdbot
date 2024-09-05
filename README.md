# TELEXKCDBOT (temporarily, already invalid name)

XKCD comics translation service **(in active development)**.

## Tech Stack
- Python 3.12;
- [FastAPI](https://fastapi.tiangolo.com/) *(for API)*;
- [aiogram](https://aiogram.dev/) *(for Telegram bot)*;
- [PostgreSQL](https://www.postgresql.org/) + [pgroonga extension](https://pgroonga.github.io/) *(as main database)*;
- [SQLAlchemy](https://www.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/en/latest/) *(as ORM)*;
- [aiohttp](https://docs.aiohttp.org/en/stable/) + [bs4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) *(for scraping)*;
- [dishka](https://dishka.readthedocs.io/en/stable/) *(for dependency injection)*;
- [Docker + Docker Compose](https://docs.docker.com/);
- [NATS](https://nats.io/) + [FastStream](https://faststream.airt.ai/latest/) + [Taskiq](https://taskiq-python.github.io/) *(for background tasks, pub-sub logic)*;
- [Redis](https://redis.io/docs/latest/) *(as cache)*;
- ...

## Dev Tech Stack
- [poetry](https://python-poetry.org/docs/) *(as dependency & package manager)*;
- [Ruff](https://docs.astral.sh/ruff/) *(as linter)*;
- [mypy](https://mypy.readthedocs.io/en/stable/) *(as type checker)*
- [pre-commit](https://pre-commit.com/) *(for git hooks)*;
- [pytest](https://docs.pytest.org/en/stable/) *(for testing)*;

### TODO:
- [ ] Fully redesign old version of telegram bot *(https://t.me/telexkcdbot)*
- [ ] Frontend *(Vue.js)*;
- [ ] logs catch, logs storage, logs visualisation *(ManticoreSearch/Loki + Vector + Grafana)*;
- [ ] 90%+ test coverage;
- [ ] Github CI;
- [ ] Database Backup;
- [ ] S3-storage adapter *(+ Minio locally)*;
- [ ] ...
