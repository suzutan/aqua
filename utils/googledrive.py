from logging import Logger
from typing import List

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive as Drive
from pydrive.drive import GoogleDriveFile

from utils.logger import getLogger
from utils.singleton import Singleton

logger: Logger = getLogger(__name__)


class GoogleDrive(Singleton):
    drive: Drive = None

    def __init__(self):
        gauth = GoogleAuth()
        gauth.CommandLineAuth()
        drive: Drive = Drive(gauth)
        self.drive = drive

    def create_folder(self, parent_id: str = "root", folder_title: str = "folder") -> (GoogleDriveFile):
        f: GoogleDriveFile = self.drive.CreateFile(
            {'parents': [{"id": parent_id}],
             'title': folder_title,
             'mimeType': 'application/vnd.google-apps.folder'})
        f.Upload()
        logger.info(f'{folder_title} has been created.')
        return f

    def create_file(self, parent_folder: GoogleDriveFile, file_name: str = "file") -> (GoogleDriveFile):
        f: GoogleDriveFile = self.drive.CreateFile(
            {'parents': [{"id": parent_folder["id"]}],
             'title': file_name,
             'mimeType': 'application/vnd.google-apps.folder'})
        f.Upload()
        logger.info(f'{file_name} has been created.')
        return f

    def fetch_file_list(self, folder_id: str, folder_only: bool = False) -> (List[GoogleDriveFile]):
        query = "'{}' in parents and trashed = false".format(folder_id)
        if folder_only:
            query = query + " and mimeType = 'application/vnd.google-apps.folder'"

        files: List[GoogleDriveFile] = self.drive.ListFile({'q': query}).GetList()

        return files
