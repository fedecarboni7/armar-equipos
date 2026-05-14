import logging

import colorlog

from app.config.settings import Settings

# Configuración del colorlog
handler = colorlog.StreamHandler()
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)s%(white)s: %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
)
handler.setFormatter(formatter)

# Configuración básica del logging
logger = logging.getLogger()
logging_level = Settings().logging_level.upper()

try:
    logger.setLevel(getattr(logging, logging_level))
except AttributeError:
    logger.setLevel(logging.INFO)

logger.addHandler(handler)


def configure_logging():
    logging.getLogger("libsql_client.dbapi2._async_executor").setLevel(logging.WARNING)
    logging.getLogger("libsql_client.dbapi2._sync_executor").setLevel(logging.WARNING)
    logging.getLogger("libsql_client.dbapi2.types").setLevel(logging.WARNING)
