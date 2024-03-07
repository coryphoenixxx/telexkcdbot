from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotConfig(BaseModel):
    token: SecretStr
    admin_id: int


class AppConfig(BaseModel):
    host: str
    port: int
    base_webhook_url: str
    webhook_path: str
    webhook_secret: str


class Settings(BaseSettings):
    bot: BotConfig
    app: AppConfig

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


def load_settings() -> Settings:
    settings = Settings()

    return settings
