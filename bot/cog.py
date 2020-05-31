import asyncio
from threading import Thread

from discord.ext import commands

from bot import App


class BackgroundCog(commands.Cog):
    def __init__(self):
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
