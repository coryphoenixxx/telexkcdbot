# noqa: N999

import os

wsgi_app = os.getenv("GUNICORN__WSGI_APP")
bind = os.getenv("GUNICORN__BIND", default="0.0.0.0:8000")
workers = os.getenv("GUNICORN__WEB_CONCURRENCY", default="3")
worker_class = os.getenv("GUNICORN__WORKER_CLASS")
