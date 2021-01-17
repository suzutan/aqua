import asyncio
import datetime
import time
from logging import Logger
from pathlib import Path
from typing import List, Optional

import requests
import tweepy
from requests import Response, Session
from tweepy import API
from tweepy.models import Status

from bot.app import App
from bot.cog import BackgroundCog
from utils.config import Config, ConfigData
from utils.googledrive import GoogleDrive as Drive
from utils.googledrive import GoogleDriveFile
from utils.logger import getLogger
from utils.twitter import twitterAPI

r: Session = requests.Session()
config: ConfigData = Config.read()
logger: Logger = getLogger(__name__)


class VTuberFanartCrawler(BackgroundCog):

    def download_media(self, target: ConfigData.VTuberFanartCrawler.Target, target_folder: GoogleDriveFile) -> (int):

        logger.info(f"download_media: {target.screen_name}")

        api: API = twitterAPI(config.vtuber_fanart_crawler.credential)

        logger.info(f"fetch tweet, count:{target.tweet_fetch_count}")
        all_statuses = tweepy.Cursor(api.user_timeline, screen_name=target.screen_name, count=200).items(target.tweet_fetch_count)
        # メディアが追加されてるツイートのみをフィルタ
        media_statuses = filter(lambda y: "media" in y.extended_entities.keys(), filter(lambda x: hasattr(x, "extended_entities"), all_statuses))

        # イラスト投稿用ハッシュタグが設定されているツイートのみフィルタ
        fanart_filtered_media_statuses = filter(lambda x: (len(x.entities["hashtags"]) > 0 and next(
            filter(lambda y: y["text"].lower() == target.fanart_hashtag.lower(), x.entities["hashtags"]), None) is not None), media_statuses)

        # file list
        logger.info("fetch google drive filelist")
        query = "'{}' in parents and trashed = false".format(target_folder["id"])
        g_media_names = list(map(lambda x: x["title"], Drive().drive.ListFile({'q': query}).GetList()))

        # GoogleDriveにuploadされていない画像だけをフィルタする
        upload_statuses: List[Status] = []
        for status in fanart_filtered_media_statuses:
            # 新しく保存する画像があるかチェック
            new_media: bool = False
            # 1ツイート複数メディア(画像)があるのでnumで連番を確保
            for num, media in enumerate(status.extended_entities["media"]):
                # リツイートされたツイートだったらリツイート元のsnを取得
                screen_name: str = status.user.screen_name \
                    if not hasattr(status, "retweeted_status") \
                    else status.retweeted_status.user.screen_name
                media_name: str = f"{status.id}_{screen_name}_{num}.{media['media_url'].split('.')[::-1][0]}"
                # 保存されてないメディアがあれば取得しにいく
                if media_name not in g_media_names:
                    new_media = True

            if new_media:
                upload_statuses.append(status)

        logger.info(f"fanart hashtag: {target.fanart_hashtag}, download tweet count: {len(upload_statuses)}")
        all_count: int = len(upload_statuses)

        # download and upload
        for count, status in enumerate(upload_statuses):
            # 新しいmediaをdiscordに通知
            [asyncio.run_coroutine_threadsafe(App.bot.get_channel(t).send(
                f"https://twitter.com/{screen_name}/status/{status.id}"), App.bot.loop) for t in target.notify_channels]
            # 1ツイート複数メディア(画像)があるのでnumで連番を確保
            for num, media in enumerate(status.extended_entities["media"]):

                # リツイートされたツイートだったらリツイート元のsnを取得
                screen_name: str = status.user.screen_name \
                    if not hasattr(status, "retweeted_status") \
                    else status.retweeted_status.user.screen_name

                media_name: str = f"{status.id}_{screen_name}_{num}.{media['media_url'].split('.')[::-1][0]}"

                # メディアがすでにgoogle driveにアップロードされていたらdownloadをスキップ
                if media_name in g_media_names:
                    logger.debug(f"target {media_name=} has been uploaded for google drive")
                    continue

                save_path: Path = (Path("images") / target.gdrive_category_folder_name / target.gdrive_folder_name / media_name)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                if save_path.exists():
                    logger.debug(f"target {media_name=} has been downloaded for local")
                    continue

                # 保存
                logger.info(f"download media: {target.fanart_hashtag=}, progress:{count+1}/{all_count}({((count+1)/all_count)*100:.1f}%), {media_name=}")

                # download
                # イベントループで実行
                media: Response = r.get(f"{media['media_url']}:large")
                if media.status_code != 200:
                    logger.error("requests failed")
                    continue

                # save local file
                with save_path.open("wb") as f:
                    f.write(media.content)
        return all_count

    def upload_media(self, target: ConfigData.VTuberFanartCrawler.Target, target_folder: GoogleDriveFile) -> (int):
        logger.info(f"upload_media: {target.screen_name}")
        image_path: Path = (Path("images") / target.gdrive_category_folder_name / target.gdrive_folder_name)

        local_file_list = list(image_path.glob("*"))
        local_file_count = len(local_file_list)
        for count, file in enumerate(local_file_list):
            metadata = {
                "title": file.name,
                "parents": [
                    {"id": target_folder["id"]}
                ]
            }
            f = Drive().drive.CreateFile(metadata)
            f.SetContentFile(str(file))
            f.Upload()
            logger.info(f"upload succssful. progress: {count+1}/{local_file_count}({((count+1)/len(local_file_list))*100:.1f}%), {str(file)=}")
            file.unlink()

        return local_file_count

    def make_and_fetch_folder(self, parent_id: str, folder_name: str) -> (Optional[GoogleDriveFile]):

        target_folder_list: List[GoogleDriveFile] = Drive().fetch_file_list(folder_id=parent_id, folder_only=True)
        target_folder: Optional[GoogleDriveFile] = next(filter(lambda x: x["title"] == folder_name, target_folder_list), None)
        if target_folder is not None:
            return target_folder

        logger.debug("create missing target folder")
        target_folder = Drive().create_folder(parent_id=parent_id, folder_title=folder_name)
        if target_folder is not None:
            return target_folder

        logger.error("failed create target folder: {folder_name}")
        return None

    def run(self):

        if not config.vtuber_fanart_crawler.enabled:
            logger.info("VTuberFanartCrawler is not enabled. cog removed.")
            self.bot.remove_cog(__name__)
            return

        while self.is_running:
            for n, target in enumerate(config.vtuber_fanart_crawler.targets):
                try:
                    logger.debug("fetch sub-category")
                    parent_id: str = config.vtuber_fanart_crawler.gdrive_root_folder_id
                    folder_name: str = target.gdrive_category_folder_name
                    subcategory_folder: GoogleDriveFile = self.make_and_fetch_folder(parent_id=parent_id, folder_name=folder_name)

                    logger.debug("fetch target folder")
                    parent_id = subcategory_folder["id"]
                    folder_name = target.gdrive_folder_name
                    target_folder: GoogleDriveFile = self.make_and_fetch_folder(parent_id=parent_id, folder_name=folder_name)

                    download_status_count: int = self.download_media(target=target, target_folder=target_folder)
                    upload_image_count: int = self.upload_media(target=target, target_folder=target_folder)
                    now: str = datetime.datetime.now().strftime('%Y/%m/%d %H:%M')
                    if download_status_count > 0:
                        asyncio.run_coroutine_threadsafe(App.bot.get_channel(config.bot.event_log_channel).send(
                            f"[VTuberFanrtCrawler] {now} crawl {target.gdrive_folder_name} Finished. {download_status_count=} {upload_image_count=}"), App.bot.loop)
                except Exception as e:
                    logger.error("failed to run", exc_info=e)
                    time.sleep(15)

            logger.info("sleep for 15 minutes")
            time.sleep(15*60)
