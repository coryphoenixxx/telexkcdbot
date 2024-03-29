from dataclasses import dataclass


@dataclass
class DBConfig:
    driver: str
    host: str
    port: int
    user: str
    password: str
    dbname: str
    echo: bool
    pool_size: int

    @property
    def dsn(self):
        return (
            f"postgresql+{self.driver}://"
            f"{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
        )
