from logging import Logger
from typing import List

import requests
from discord import Embed, Message
from discord.ext import commands
from requests import Session

from bot.cog import BaseCog
from utils.config import Config, ConfigData
from utils.googledrive import GoogleDrive as Drive
from utils.googledrive import GoogleDriveFile
from utils.logger import getLogger

drive: Drive = Drive()
config: ConfigData = Config.read()

r: Session = requests.Session()
logger: Logger = getLogger(__name__)


class CmdFanart(BaseCog):

    @commands.group()
    async def fanart(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('subcommand is required')

    @fanart.command()
    async def list(self, ctx):
        logger.info("fetch VTuberFanartCrawler image count")
        embed = Embed(title="Fanart Image Count",
                      description="fetch image. please wait for while...",
                      color=0x80fffd)

        embed.set_footer(text="VTuberFanartCounter")

        logger.debug("send embed message")

        message: Message = await ctx.channel.send(embed=embed)

        async with ctx.channel.typing():
            logger.debug("fetch subfolder list")
            subfolders: List[GoogleDriveFile] = \
                drive.fetch_file_list(folder_id=config.vtuber_fanart_crawler.gdrive_root_folder_id, folder_only=True)

            logger.debug("fetch file list in subfolder")
            fetch_folders: List[dict] = [{"files": drive.fetch_file_list(folder_id=folder["id"]), "folder": folder} for folder in subfolders]
            logger.debug("adding embed")
            [embed.add_field(name=data["folder"]["title"], value=len(data["files"]), inline=False) for data in fetch_folders]
            embed.description = "all count: {}".format(sum(len(folder["files"]) for folder in fetch_folders))
            logger.debug("send editted embed")
            embed.color = 0x309c40
            await message.edit(embed=embed)
