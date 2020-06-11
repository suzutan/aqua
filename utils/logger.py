from logging import DEBUG, INFO, Formatter, Logger, StreamHandler
from logging import getLogger as origin_getLogger

from utils.config import Config, ConfigData

config: ConfigData = Config().read()


def getLogger(name: str) -> Logger:
    logger = origin_getLogger(name)
    handler = StreamHandler()
    handler.setFormatter(Formatter("level=%(levelname)s\ttime=%(asctime)s\tname=%(name)s\tmessage=%(message)s"))
    logger.setLevel(INFO)

    if config.debug:
        logger.setLevel(DEBUG)

    logger.addHandler(handler)
    logger.propagate = False

    return logger
