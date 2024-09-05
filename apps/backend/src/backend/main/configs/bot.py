from dataclasses import dataclass
from enum import Enum


class BotRunMode(Enum):
    POLLING = "POLLING"
    WEBHOOK = "WEBHOOK"


@dataclass(slots=True)
class BotAppConfig:
    host: str
    port: int


@dataclass(slots=True)
class WebhookConfig:
    url: str
    path: str
    secret_token: str


@dataclass(slots=True)
class BotConfig:
    token: str
    admin_id: int
    run_method: BotRunMode
    app: BotAppConfig
    webhook: WebhookConfig
