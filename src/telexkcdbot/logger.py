from loguru import logger
from src.telexkcdbot.config import BASE_DIR


LOGS_PATH = BASE_DIR.joinpath('logs')

logger.add(f'{LOGS_PATH}/actions.log', rotation='5 MB', level='INFO')
logger.add(f'{LOGS_PATH}/errors.log', rotation='500 KB', level='ERROR', backtrace=True, diagnose=True)
logger.error("Log files created...")  # Creates both log files
