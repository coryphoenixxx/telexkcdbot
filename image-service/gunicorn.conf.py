from src.config import load_config

app_config = load_config()

bind = [f"{app_config.host}:{app_config.port}"]
workers = app_config.worker_num
errorlog = '-'
keepalive = 5
