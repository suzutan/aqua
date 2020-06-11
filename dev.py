import bpython
from discord.ext import commands
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from tweepy import API

from utils.config import Config
from utils.twitter import twitterAPI

config = Config.read()


api: API = twitterAPI(config.vtuber_fanart_crawler.credential)

gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

bot = commands.Bot(command_prefix=config.bot.prefix)

bpython.embed(locals_=locals())
