from loguru import logger
from src.bot.paths import LOGS_PATH


logger.add(f'{LOGS_PATH}/actions.log', rotation='5 MB', level='INFO')
logger.add(f'{LOGS_PATH}/errors.log', rotation='500 KB', level='ERROR', backtrace=True, diagnose=True)
