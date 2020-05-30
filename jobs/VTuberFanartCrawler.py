import asyncio
import threading
from logging import Logger
from pathlib import Path
from typing import List

import requests
import tweepy
from requests import Response, Session
from tweepy import API
from tweepy.models import Status
from utils.config import Config
from utils.googledrive import GoogleDrive as Drive
from utils.googledrive import GoogleDriveFile
from utils.logger import getLogger
from utils.twitter import OAuth1Credentials, Twitter

drive: Drive = Drive().drive
r: Session = requests.Session()
c = Config()
logger: Logger = getLogger(__name__)


class VTuberFanartCrawler:

    async def download_media(self, target: dict, media_folders: List[GoogleDriveFile]):

        logger.info(f"download_media: {target['screen_name']}")

        api: API = Twitter(OAuth1Credentials(c)).get_api()

        fetch_count: int = c.get_user_media["global_tweet_fetch_count"]
        if "tweet_fetch_count" in target.keys():
            fetch_count = target["tweet_fetch_count"]
            # 対象snのツイート3200件を取得

        logger.info(f"fetch tweet, count:{fetch_count}")
        all_statuses = tweepy.Cursor(api.user_timeline, screen_name=target["screen_name"], count=200).items(fetch_count)
        # メディアが追加されてるツイートのみをフィルタ
        media_statuses = filter(lambda y: "media" in y.extended_entities.keys(), filter(lambda x: hasattr(x, "extended_entities"), all_statuses))

        # イラスト投稿用ハッシュタグが設定されているツイートのみフィルタ
        fanart_filtered_media_statuses = filter(lambda x: (len(x.entities["hashtags"]) > 0 and next(
            filter(lambda y: y["text"].lower() == target["fanart_hashtag"].lower(), x.entities["hashtags"]), None) is not None), media_statuses)

        # save media
        target_folder = next(filter(lambda x: x["title"] == target["gdrive_folder_name"], media_folders), None)
        if target_folder is None:
            logger.error("failed fetch target_folder")
            return

        # file list
        logger.info("fetch google drive filelist")
        query = "'{}' in parents and trashed = false".format(target_folder["id"])
        g_media_names = list(map(lambda x: x["title"], drive.ListFile({'q': query}).GetList()))

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

        logger.info(f"fanart hashtag: {target['fanart_hashtag']}, download tweet count: {len(upload_statuses)}")
        all_count: int = len(upload_statuses)

        # download and upload
        for count, status in enumerate(upload_statuses):
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

                save_path: Path = (Path("images") / target["gdrive_folder_name"] / media_name)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                if save_path.exists():
                    logger.debug(f"target {media_name=} has been downloaded for local")
                    continue

                # 保存
                logger.info(f"download media: {target['fanart_hashtag']=}, progress:{count+1}/{all_count}({((count+1)/all_count)*100:.1f}%), {media_name=}")

                # download
                loop = asyncio.get_event_loop()
                # イベントループで実行
                media: Response = await loop.run_in_executor(None, r.get, f"{media['media_url']}:large")
                if media.status_code != 200:
                    logger.error("requests failed")
                    continue

                # save local file
                with save_path.open("wb") as f:
                    f.write(media.content)

    async def upload_media(self, target: dict, media_folders: List[GoogleDriveFile]):
        logger.info(f"upload_media: {target['screen_name']}")
        image_path: Path = (Path("images") / target["gdrive_folder_name"])
        # save media
        target_folder = next(filter(lambda x: x["title"] == target["gdrive_folder_name"], media_folders), None)
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
            f = drive.CreateFile(metadata)
            f.SetContentFile(str(file))
            f.Upload()
            logger.info(f"upload succssful. progress: {count+1}/{local_file_count}({((count+1)/len(local_file_list))*100:.1f}%), {str(file)=}")
            file.unlink()

    async def do(self, target: dict, media_folders: List[GoogleDriveFile]):

        logger.info(f"do {target['screen_name']=}")
        await self.download_media(target, media_folders)
        await self.upload_media(target, media_folders)
        logger.info(f"finish {__name__=}")

    async def __execute(self,):
        logger.info("start get_user_media")

        # media作成
        query = "'{}' in parents and trashed = false and mimeType = 'application/vnd.google-apps.folder'" \
            .format(c.get_user_media["gdrive_root_folder_id"])
        media_folders: List[GoogleDriveFile] = drive.ListFile({'q': query}).GetList()

        logger.debug("fetch current filder list")
        targets = c.get_user_media["targets"]
        new_folder_names = list(map(lambda x: x["gdrive_folder_name"],
                                    filter(lambda x: x["gdrive_folder_name"] not in list(map(lambda y: y["title"], media_folders)), targets)))

        logger.info("create sub folder if not exists")
        for folder_name in new_folder_names:
            media_folders.append(Drive().create_folder(parent_id=c.get_user_media["gdrive_root_folder_id"], folder_title=folder_name))
            logger.info(f"[create] {folder_name=} has been created.")

        while True:
            for n, target in enumerate(targets):
                try:
                    await self.do(target, media_folders)
                except Exception as e:
                    logger.error(e)

            logger.info("sleep for 10 minutes")
            await asyncio.sleep(15 * 60)

    def execute(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.__execute())
