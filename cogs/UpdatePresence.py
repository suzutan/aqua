import asyncio
import random
from logging import Logger
from typing import List
from bot import App
from bot.cog import BackgroundCog
from discord import Game, Status, Streaming
from utils.logger import getLogger
from utils.config import Config
logger: Logger = getLogger(__name__)
c: Config = Config()
pc = c.read()["plugins"][__name__.split(".")[-1]]


class UpdatePresence(BackgroundCog):
    async def run(self):
        logger.info("run")
        await App.bot.change_presence(status=Status.online)

        while self.is_running:
            try:
                status: str = random.choice(pc["activities"])
                logger.info(f"set status: {status}")
                await App.bot.change_presence(activity=Streaming(name=status, url="https://www.youtube.com/channel/UC1opHUrw8rvnsadT-iGp7Cg"))
            except Exception as e:
                logger.error("does not change presense.", exc_info=e)
            finally:
                await asyncio.sleep(1 * 60)
