from dataclasses import dataclass


@dataclass(slots=True)
class DbConfig:
    host: str
    port: int
    user: str
    password: str
    dbname: str
    echo: bool
    pool_size: int
