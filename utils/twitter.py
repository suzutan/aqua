from logging import Logger

from tweepy import API, OAuthHandler

from utils.config import Config
from utils.logger import getLogger
from utils.singleton import Singleton

logger: Logger = getLogger(__name__)


class OAuth1Credentials:
    ck: str = None
    cs: str = None
    at: str = None
    ats: str = None

    def __init__(self, config: Config):

        if "twitter" not in config.read().keys():
            logger.error("twitter config  is not defined")
            raise AttributeError("twitter config  is not defined")

        tw = config.read()["twitter"]
        if "" in tw.values():
            logger.error("credentials is not valid")
            raise AttributeError("twitter credentials is not valid")

        self.ck = tw["ck"]
        self.cs = tw["cs"]
        self.at = tw["at"]
        self.ats = tw["ats"]


class Twitter(Singleton):
    api: API = None

    def __init__(self, credential: OAuth1Credentials):
        oauth = OAuthHandler(credential.ck, credential.cs)
        oauth.set_access_token(credential.at, credential.ats)
        self.api = API(oauth)

    def get_api(self) -> API:
        return self.api
