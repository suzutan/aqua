import asyncio
import random
from logging import Logger
from typing import List

from discord import Game, Status

from bot import App
from bot.cog import BackgroundCog
from utils.config import Config, ConfigData
from utils.logger import getLogger

logger: Logger = getLogger(__name__)

config: ConfigData = Config.read()

activities: List[str] = config.bot.presences


class UpdatePresence(BackgroundCog):
    async def run(self):
        await App.bot.change_presence(status=Status.online)

        while self.is_running:
            try:
                status: str = random.choice(activities)
                logger.info(f"set status: {status}")
                await App.bot.change_presence(activity=Game(name=status))
            except Exception as e:
                logger.error("does not change presense.", exc_info=e)
            finally:
                await asyncio.sleep(1 * 60)
