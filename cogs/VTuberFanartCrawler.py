import asyncio
import time
from logging import Logger
from pathlib import Path
from typing import List

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
config: ConfigData.VTuberFanartCrawler = Config.read().vtuber_fanart_crawler
logger: Logger = getLogger(__name__)


class VTuberFanartCrawler(BackgroundCog):

    def download_media(self, target: ConfigData.VTuberFanartCrawler.Target, media_folders: List[GoogleDriveFile]):

        logger.info(f"download_media: {target.screen_name}")

        api: API = twitterAPI(config.credential)

        logger.info(f"fetch tweet, count:{target.tweet_fetch_count}")
        all_statuses = tweepy.Cursor(api.user_timeline, screen_name=target.screen_name, count=200).items(target.tweet_fetch_count)
        # メディアが追加されてるツイートのみをフィルタ
        media_statuses = filter(lambda y: "media" in y.extended_entities.keys(), filter(lambda x: hasattr(x, "extended_entities"), all_statuses))

        # イラスト投稿用ハッシュタグが設定されているツイートのみフィルタ
        fanart_filtered_media_statuses = filter(lambda x: (len(x.entities["hashtags"]) > 0 and next(
            filter(lambda y: y["text"].lower() == target.fanart_hashtag.lower(), x.entities["hashtags"]), None) is not None), media_statuses)

        # save media
        target_folder = next(filter(lambda x: x["title"] == target.gdrive_folder_name, media_folders), None)
        if target_folder is None:
            logger.error("failed fetch target_folder")
            return

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

                save_path: Path = (Path("images") / target.gdrive_folder_name / media_name)
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

    def upload_media(self, target: ConfigData.VTuberFanartCrawler.Target, media_folders: List[GoogleDriveFile]):
        logger.info(f"upload_media: {target.screen_name}")
        image_path: Path = (Path("images") / target.gdrive_folder_name)
        # save media
        target_folder = next(filter(lambda x: x["title"] == target.gdrive_folder_name, media_folders), None)
        if target_folder is None:
            logger.error("failed fetch target_folder")
            return

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

    def run(self):

        if not config.enabled:
            logger.info("VTuberFanartCrawler is not enabled. cog removed.")
            self.bot.remove_cog(__name__)
            return

        # media作成
        query = "'{}' in parents and trashed = false and mimeType = 'application/vnd.google-apps.folder'" \
            .format(config.gdrive_root_folder_id)
        media_folders: List[GoogleDriveFile] = Drive().drive.ListFile({'q': query}).GetList()
        media_folders_name: List[str] = list(map(lambda y: y["title"], media_folders))

        logger.debug("fetch current filder list")
        targets: List[ConfigData.VTuberFanartCrawler.Target] = config.targets
        new_folder_names = list(map(lambda x: x.gdrive_folder_name, filter(lambda x: x.gdrive_folder_name not in media_folders_name, targets)))

        if len(new_folder_names) > 0:
            logger.info(f"create sub folder. count:{len(new_folder_names)}")
            for folder_name in new_folder_names:
                media_folders.append(Drive().create_folder(parent_id=config.gdrive_root_folder_id, folder_title=folder_name))
                logger.info(f"create folder: {folder_name=}")

        while self.is_running:
            for n, target in enumerate(targets):
                try:
                    self.download_media(target, media_folders)
                    self.upload_media(target, media_folders)
                except Exception as e:
                    logger.error("failed to run", exc_info=e)
                    time.sleep(15)

            logger.info("sleep for 15 minutes")
            time.sleep(15*60)
