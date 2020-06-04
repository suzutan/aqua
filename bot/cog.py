import asyncio
from threading import Thread

from discord.ext import commands

from bot import App


class BaseCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot


class BackgroundCog(BaseCog):

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        App.bot.loop.create_task(self.__wrap())

    def run(self):
        raise NotImplementedError()

    async def __wrap(self):
        await App.bot.wait_until_ready()

        if asyncio.iscoroutinefunction(self.run):
            await self.run()
        else:
            thread = Thread(target=self.run)
            thread.setDaemon(True)
            thread.start()

    @property
    def is_running(self) -> bool:
        return App.bot.loop.is_running()
