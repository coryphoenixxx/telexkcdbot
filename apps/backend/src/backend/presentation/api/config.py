from dataclasses import dataclass


@dataclass
class APIConfig:
    host: str
    port: int
