from pathlib import Path


BASE_DIR = Path(__file__).parent.parent.parent
IMG_PATH = BASE_DIR.joinpath('static/img')
LOGS_PATH = BASE_DIR.joinpath('logs')
PATH_TO_RU_COMICS_DATA = BASE_DIR.joinpath('static/ru_comics_data')
