import asyncio
from logging import Logger
from typing import List, Optional

import tweepy
from tweepy import API as TwitterAPI
from tweepy.models import List as TwitterList

from bot.cog import BackgroundCog
from utils.config import Config, ConfigData
from utils.logger import getLogger
from utils.twitter import twitterAPI

config: ConfigData = Config.read()

logger: Logger = getLogger(__name__)


class TwitterSyncList(BackgroundCog):

    def _chunks(self, split_list, n):
        for i in range(0, len(split_list), n):
            yield split_list[i: i + n]

    def get_list(self, api: TwitterAPI, slug: str) -> (TwitterList):
        current_lists: List[TwitterList] = api.lists_all()
        target_list: TwitterList = next(
            filter(lambda i: i.slug == slug, current_lists), None)
        return target_list

    def create_list(self, api: TwitterAPI, **kwargs) -> (TwitterList, bool):
        name: str = kwargs.get("name", "follows")
        mode: str = kwargs.get("mode", "private")
        description: str = kwargs.get("description", "follow list")

        follows: TwitterList = api.create_list(
            name=name, mode=mode, description=description)
        logger.info("list created.")

        return follows, (follows is not None)

    def __convert_sn_to_id(self, api: TwitterAPI, screen_name: str) -> (Optional[int]):
        user: tweepy.models.User = api.get_user(screen_name=screen_name)

        return None if not user else user.id

    def do(self, account: ConfigData.TwitterSyncList):

        api: TwitterAPI = twitterAPI(account.credential)
        slug: str = account.slug

        target_list: TwitterList = self.get_list(api=api, slug=slug)
        # create follow list if not exist
        if target_list is None:
            logger.warn(f"{slug=} does not exists. processing create...")
            target_list, result = self.create_list(api=api, name=slug)
            if not result:
                raise Exception("List {slug=} does not created.")

        # 同期したいユーザーのid一覧を取得
        if account.is_sync_follows:
            logger.debug("sync follows")
            target_ids: List[int] = api.friends_ids()
        else:
            logger.debug("sync manual users")
            target_ids: List[int] = list(map(lambda x: self.__convert_sn_to_id(api=api, screen_name=x), account.target_screen_names))

        # 既存のfollowsリストのメンバー一覧を取得
        current_members: List[int] = [
            i.id for i in api.list_members(list_id=target_list.id, count=5000)]
        # listに追加する新規friendsを算出(friends - current_members = add_target)
        add_targets: List[int] = list(
            filter(lambda x: x not in current_members, target_ids))
        # listから削除するリムーブしたfriendsを算出(current_members - friends = remove_target)
        remove_targets: List[int] = list(
            filter(lambda x: x not in target_ids, current_members))

        logger.info(
            "exec: screen_name:{} slug:{} add:{} remove:{} diff:{}".format(
                api.me().screen_name,
                slug,
                len(add_targets),
                len(remove_targets),
                len(add_targets) - len(remove_targets)
            ))

        # add
        for chunked_user_ids in self._chunks(add_targets, 100):
            result = api.add_list_members(list_id=target_list.id,
                                          user_id=chunked_user_ids)
            logger.debug(f"slug:{slug} add member count:{len(chunked_user_ids)}")

        # remove
        for chunked_user_ids in self._chunks(remove_targets, 100):
            result = api.remove_list_members(list_id=target_list.id,
                                             user_id=chunked_user_ids)
            logger.debug(f"slug:{slug} remove member count:{len(chunked_user_ids)}")

    async def run(self):

        if next(filter(lambda x: x.enabled is True, config.twitter_sync_list), None) is None:
            logger.info("TwitterSyncList is not enabled. cog removed.")
            self.bot.remove_cog(__name__)
            return

        while self.is_running:
            logger.debug(f"execute {__name__=}")
            for account in filter(lambda x: x.enabled, config.twitter_sync_list):
                try:
                    self.do(account=account)
                except Exception as e:
                    logger.error(e)
            logger.debug(f"finish {__name__=}")
            await asyncio.sleep(15 * 60)
