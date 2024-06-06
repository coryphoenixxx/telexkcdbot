from dataclasses import dataclass

from shared.config_loader import load_config


@dataclass
class GunicornConfig:
    wsgi_app: str
    bind: str
    workers: int
    worker_class: str


config_ = load_config(GunicornConfig, scope="gunicorn")

wsgi_app = config_.wsgi_app
bind = config_.bind
workers = config_.workers
worker_class = config_.worker_class
