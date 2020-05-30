from logging import INFO, Formatter, Logger, StreamHandler
from logging import getLogger as origin_getLogger


def getLogger(name: str) -> Logger:
    logger = origin_getLogger(name)
    handler = StreamHandler()
    handler.setFormatter(Formatter("level=%(levelname)s\ttime=%(asctime)s\tname=%(name)s\tmessage=%(message)s"))
    handler.setLevel(INFO)
    logger.setLevel(INFO)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
