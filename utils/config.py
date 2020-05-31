import os
from logging import Logger
from pathlib import Path
from typing import Optional

import yaml
from utils.singleton import Singleton


class Config(Singleton):
    __config: dict = None

    def __getattr__(self, name):
        return self.__config.__getitem__(name)

    def __init__(self):

        app_env: str = Config.__read_env("APP_ENV", "development")
        config_dir: Path = Path("config")
        default_config_path: Path = (config_dir / "default.yaml")
        env_config_path: Path = (config_dir / f"{app_env}.yaml")

        default_config: dict = {}
        env_config: dict = {}
        resolved_config: dict = {}

        # env config check
        if not env_config_path.exists():
            raise FileNotFoundError(f"failed load env config({app_env=})")

        # resolve config
        with default_config_path.open("r") as f:
            default_config = yaml.load(f, Loader=yaml.SafeLoader)
        with env_config_path.open("r") as f:
            env_config = yaml.load(f, Loader=yaml.SafeLoader)
        resolved_config = self.__merge(default_config, env_config)

        self.__config = resolved_config

    @staticmethod
    def __read_env(env_name: str,
                   default: Optional[str] = None) -> (Optional[str]):
        if env_name not in os.environ.keys():
            return default

        return os.environ["APP_ENV"]

    def __merge(self, old: dict, new: dict) -> dict:
        if isinstance(old, dict) and isinstance(new, dict):
            for k, v in old.items():
                new[k] = self.__merge(v, new[k]) if k in new else v
        return new

    def read(self) -> dict:

        return self.__config
