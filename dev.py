import bpython
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from tweepy import API
from utils.config import Config
from utils.twitter import OAuth1Credentials, Twitter

api: API = Twitter(
    OAuth1Credentials(Config())).get_api()

gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)


bpython.embed(locals_=locals())
