from logging import Logger

from tweepy import API, OAuthHandler

from utils.config import ConfigData
from utils.logger import getLogger

logger: Logger = getLogger(__name__)


def twitterAPI(credential: ConfigData.TwitterSyncList.Credential) -> (API):
    oauth = OAuthHandler(credential.ck, credential.cs)
    oauth.set_access_token(credential.at, credential.ats)
    return API(oauth)
