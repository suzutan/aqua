import asyncio
import importlib
from logging import Logger
from pathlib import Path

from utils.logger import getLogger

logger: Logger = getLogger(__name__)
job_dir: str = "jobs"


def execute():
    for filename in filter(lambda x: not x.name == "__init__.py", Path(job_dir).glob("*.py")):
        name: str = filename.name.replace(".py", "")

        try:
            mod = importlib.import_module(f"{job_dir}.{name}")
        except Exception as e:
            logger.exception(f"Job: {name} could not loaded.", exc_info=e)
            continue

        if (job := getattr(mod, name, None)) and isinstance(job, type):
            try:
                job().execute()
                logger.info(f"Job: {name} loaded.")
            except Exception as e:
                logger.exception(f"Job: {name} could not loaded.", exc_info=e)

    loop = asyncio.get_event_loop()
    loop.run_forever()


if __name__ == "__main__":
    logger.info(f"execute {__name__=}")
    execute()
