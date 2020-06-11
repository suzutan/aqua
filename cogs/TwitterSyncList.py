import asyncio
from logging import Logger
from typing import List

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

    def do(self, account: ConfigData.TwitterSyncList) -> bool:
        api: TwitterAPI = twitterAPI(account.credential)
        slug: str = account.slug

        follows: TwitterList = self.get_list(api=api, slug=slug)

        # create follow list if not exist
        if follows is None:
            logger.warn(f"{slug=} does not exists")
            follows, result = self.create_list(api=api, name=slug)
            if not result:
                logger.error("follows list does not created.")
                return False

        # 現在フォローしているid一覧を取得
        friends_ids: List[int] = api.friends_ids()
        # 既存のfollowsリストのメンバー一覧を取得
        list_members: List[int] = [
            i.id for i in api.list_members(list_id=follows.id, count=5000)]

        # listに追加する新規friendsを算出(friends - list_members = add_target)
        add_targets: List[int] = list(
            filter(lambda x: x not in list_members, friends_ids))
        # listから削除するリムーブしたfriendsを算出(list_members - friends = remove_target)
        remove_targets: List[int] = list(
            filter(lambda x: x not in friends_ids, list_members))

        logger.info(
            "exec: add:{} remove:{} diff:{}".format(
                len(add_targets),
                len(remove_targets),
                len(add_targets) - len(remove_targets)
            ))

        before_member_count: int = follows.member_count
        # add
        for chunked_user_ids in self._chunks(add_targets, 100):
            result = api.add_list_members(list_id=follows.id,
                                          user_id=chunked_user_ids)
            logger.info(f"add member count:{len(chunked_user_ids)}")

        # remove
        for chunked_user_ids in self._chunks(remove_targets, 100):
            result = api.add_list_members(list_id=follows.id,
                                          user_id=chunked_user_ids)
            logger.info(f"remove member count:{len(chunked_user_ids)}")

        follows: TwitterList = self.get_list(api=api, slug=slug)
        after_member_count: int = follows.member_count
        logger.info(
            "result: before:{} after:{} diff:{}".format(
                before_member_count,
                after_member_count,
                before_member_count - after_member_count
            ))

        return True

    async def run(self):

        if next(filter(lambda x: x.enabled is True, config.twitter_sync_list), None) is None:
            logger.info("TwitterSyncList is not enabled. cog removed.")
            self.bot.remove_cog(__name__)
            return

        while self.is_running:
            logger.info(f"execute {__name__=}")
            for account in config.twitter_sync_list:
                try:
                    self.do(account=account)
                except Exception as e:
                    logger.error(e)
            logger.info(f"finish {__name__=}")
            await asyncio.sleep(15 * 60)
