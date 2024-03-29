from dataclasses import dataclass, field


@dataclass
class BotConfig:
    token: str
    admin_id: int


@dataclass
class AppConfig:
    host: str
    port: int
    webhook_url: str
    webhook_path: str
    webhook_secret: str


@dataclass
class Config:
    bot: BotConfig = field(default_factory=BotConfig)
    app: AppConfig = field(default_factory=AppConfig)
