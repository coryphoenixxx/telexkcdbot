from loguru import logger
from src.config import LOGS_DIR

logger.add(f"{LOGS_DIR}/actions.log", rotation="5 MB", level="INFO")

logger.add(
    f"{LOGS_DIR}/errors.log",
    rotation="500 KB",
    level="ERROR",
    backtrace=True,
    diagnose=True,
)
