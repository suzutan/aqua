import importlib
from logging import INFO, Formatter, Logger, StreamHandler
from pathlib import Path

from aiohttp import ClientSession
from discord import Game, Status
from discord.ext import commands
from utils.config import Config, ConfigData
from utils.logger import getLogger as origin_getLogger

RESOURCES_DIR: str = "resources"
CACHE_DIR: str = "cache"
COGS_DIR: str = "cogs"


class App:
    bot: commands.Bot
    config: ConfigData
    logger: Logger
    session: ClientSession

    @classmethod
    def run(cls):

        cls.logger = origin_getLogger(__name__)
        cls.config = Config.read()
        cls.session = ClientSession(raise_for_status=True)
        cls.bot = commands.Bot(command_prefix=cls.config.bot.prefix or "!",
                               status=Status.dnd, activity=Game("起動中..."))
        cls.__load_cogs()
        cls.bot.run(cls.config.bot.token)

    @classmethod
    def __load_cogs(cls):
        for cog in Path(COGS_DIR).glob("*.py"):

            name = cog.name.replace(".py", "")
            try:
                mod = importlib.import_module(f"{COGS_DIR}.{name}")
            except Exception as e:
                cls.logger.exception(
                    f"Cog: {name} could not loaded.", exc_info=e)

                continue

            if (cog := getattr(mod, name, None)) and isinstance(cog, type) and issubclass(cog, commands.Cog):
                try:
                    cls.bot.add_cog(cog(cls.bot))

                    cls.logger.info(f"Cog: {name} loaded.")
                except Exception as e:
                    cls.logger.exception(
                        f"Cog: {name} could not loaded.", exc_info=e)
            else:
                cls.logger.error(f"failed to load {name}.")
