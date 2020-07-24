import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import yaml
from typing import List
from utils.singleton import Singleton


@dataclass
class ConfigData:
    @dataclass
    class Bot:
        prefix: str
        token: str
        presences: List[str]
        event_log_channel: int

    @dataclass
    class TwitterSyncList:
        @dataclass
        class Credential:
            ck: str
            cs: str
            at: str
            ats: str

        enabled: str
        slug: str
        credential: Credential
        is_sync_follows: bool
        target_screen_names: List[str]

    @dataclass
    class VTuberFanartCrawler:

        @dataclass
        class Credential:
            ck: str
            cs: str
            at: str
            ats: str

        @dataclass
        class Target:
            screen_name: str
            gdrive_category_folder_name: str
            gdrive_folder_name: str
            fanart_hashtag: str
            tweet_fetch_count: int
            notify_channels: List[int]

        enabled: bool
        credential: Credential
        gdrive_root_folder_id: str
        targets: List[Target]

    debug: bool
    bot: Bot
    twitter_sync_list: List[TwitterSyncList]
    vtuber_fanart_crawler: VTuberFanartCrawler


class Config(Singleton):
    config: ConfigData = None

    def __init__(self):

        app_env: str = Config.__read_env("APP_ENV", "development")
        config_dir: Path = Path("config")
        default_config_path: Path = (config_dir / "default.yaml")
        env_config_path: Path = (config_dir / f"{app_env}.yaml")

        default_config: dict = {}
        env_config: dict = {}
        r: dict = {}

        # env config check
        if not env_config_path.exists():
            raise FileNotFoundError(f"failed load env config({app_env=})")

        # resolve config
        with default_config_path.open("r") as f:
            default_config = yaml.load(f, Loader=yaml.SafeLoader)
        with env_config_path.open("r") as f:
            env_config = yaml.load(f, Loader=yaml.SafeLoader)
        r = self.__merge(default_config, env_config)

        data = ConfigData(
            debug=r["debug"],
            bot=ConfigData.Bot(
                prefix=r["bot"]["prefix"],
                token=r["bot"]["token"],
                presences=r["bot"]["presences"],
                event_log_channel=r["bot"]["event_log_channel"],
            ),
            twitter_sync_list=list(map(lambda x: ConfigData.TwitterSyncList(
                enabled=x["enabled"],
                slug=x["slug"],
                credential=ConfigData.TwitterSyncList.Credential(**x["credential"]),
                is_sync_follows=False if "is_sync_follows" not in x.keys() else x["is_sync_follows"],  # keyがなければデフォルトfalse
                target_screen_names=[] if "target_screen_names" not in x.keys() else x["target_screen_names"],  # target_screen_namesがなければからっぽ
            ), r["TwitterSyncList"])),
            vtuber_fanart_crawler=ConfigData.VTuberFanartCrawler(
                enabled=r["VTuberFanartCrawler"]["enabled"],
                credential=ConfigData.VTuberFanartCrawler.Credential(**r["VTuberFanartCrawler"]["credential"]),
                gdrive_root_folder_id=r["VTuberFanartCrawler"]["gdrive_root_folder_id"],
                targets=list(map(lambda x: ConfigData.VTuberFanartCrawler.Target(
                    screen_name=x["screen_name"],
                    gdrive_category_folder_name=x["gdrive_category_folder_name"],
                    gdrive_folder_name=x["gdrive_folder_name"],
                    fanart_hashtag=x["fanart_hashtag"],
                    tweet_fetch_count=x["tweet_fetch_count"],
                    notify_channels=x["notify_channels"],
                ), r["VTuberFanartCrawler"]["targets"]))
            )
        )

        self.config = data

    @ staticmethod
    def __read_env(env_name: str, default: Optional[str] = None) -> (Optional[str]):

        return default if env_name not in os.environ.keys() else os.environ["APP_ENV"]

    def __merge(self, old: dict, new: dict) -> (dict):
        if isinstance(old, dict) and isinstance(new, dict):
            for k, v in old.items():
                new[k] = self.__merge(v, new[k]) if k in new else v
        return new

    @classmethod
    def read(cls) -> ConfigData:
        return Config().config
