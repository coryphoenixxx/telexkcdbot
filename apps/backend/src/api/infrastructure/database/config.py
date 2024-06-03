from dataclasses import dataclass


@dataclass
class DbConfig:
    driver: str
    host: str
    port: int
    user: str
    password: str
    dbname: str
    echo: bool
    pool_size: int
