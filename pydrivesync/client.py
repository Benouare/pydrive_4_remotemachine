import hashlib
import os
import shutil

import pkg_resources
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from pydrivesync import constance
from pydrivesync.ThreadDownloader import Downloader


class PyDriveSync():

    DRIVE_PATH = "google_drive/"
    current_files = dict()
    current_remote_files = []
    threads = []
    drive = None
    GOOGLE_MIME = [
        "application/vnd.google-apps.folder",
        "application/vnd.google-apps.audio",
        "application/vnd.google-apps.document"
        "application/vnd.google-apps.drive-sdk",
        "application/vnd.google-apps.drawing",
        "application/vnd.google-apps.file",
        "application/vnd.google-apps.folder",
        "application/vnd.google-apps.form",
        "application/vnd.google-apps.fusiontable",
        "application/vnd.google-apps.map",
        "application/vnd.google-apps.photo",
        "application/vnd.google-apps.presentation",
        "application/vnd.google-apps.script",
        "application/vnd.google-apps.shortcut",
        "application/vnd.google-apps.site",
        "application/vnd.google-apps.spreadsheet",
        "application/vnd.google-apps.unknown",
        "application/vnd.google-apps.video"
    ]
    error_files = []
    gdriveIds = []
    mimetypes = {
        # Drive Document files as MS Word files.
        'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        # Drive Sheets files as MS Excel files.
        'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        "application/vnd.google-apps.presentation": 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        # etc.
    }

    def md5(self, fname):
        with open(fname, "rb") as file:
            return hashlib.md5(file.read()).hexdigest()

    def list_all_files(self, path):
        objects = os.listdir(path)
        for file in objects:
            current_file = {
                "path": os.path.join(path, file),
                "is_file": os.path.isfile(os.path.join(path, file))
            }
            self.current_files[current_file["path"]] = current_file
            if not os.path.isfile(os.path.join(path, file)):
                self.list_all_files(os.path.join(path, file))

    def list_all_files_google(self, id, name=None):
        if name is None:
            if id == "root":
                params = {
                    'q': "'{}' in parents and trashed=false".format(id)
                }
            else:
                params = {
                    'q': "'{}' in parents and trashed=false".format(id),
                    'corpora': 'teamDrive',
                    'teamDriveId': '{}'.format(id),
                    'includeTeamDriveItems': True,
                    'supportsTeamDrives': True
                }
        else:
            params = {
                'q': "'{}' in parents and trashed=false".format(id),
                'includeTeamDriveItems': True,
                'supportsTeamDrives': True
            }
        files = self.drive.ListFile(params).GetList()

        files = sorted(
            files, key=lambda file: int(file['fileSize']) if 'fileSize' in file else 0)

        for file in files:
            # no_delete = ['kind', 'id', 'etag', 'selfLink', 'webContentLink', 'alternateLink', 'embedLink', 'iconLink', 'thumbnailLink', 'title', 'mimeType', 'labels', 'copyRequiresWriterPermission', 'createdDate', 'modifiedDate', 'modifiedByMeDate', 'lastViewedByMeDate', 'markedViewedByMeDate','version', 'parents', 'exportLinks', 'userPermission', 'quotaBytesUsed', 'ownerNames', 'owners', 'lastModifyingUserName', 'lastModifyingUser', 'capabilities', 'editable', 'copyable', 'writersCanShare', 'shared', 'explicitlyTrashed', 'appDataContents', 'spaces']
            no_delete = ["title", "mimeType", "id", "md5Checksum"]
            # keys = list(file.keys())
            # for key in keys:
            #    if key not in no_delete:
            #        del file[key]
            if name:
                file["title"] = os.path.join(name, file["title"])
            if file["mimeType"] == "application/vnd.google-apps.folder":
                try:
                    self.list_all_files_google(
                        "{}".format(file["id"]), file["title"])
                except Exception as e:
                    print("error {}".format(file["title"]))
                    print(e)
            self.download(file)
        del files

    def download(self, file):
        print("###")
        print("Processing remote file {} ({}  {})".format(
            file['title'], file["mimeType"], file["fileSize"] if "fileSize" in file else 0))
        if file["mimeType"] == "application/vnd.google-apps.folder":
            if not os.path.exists(os.path.join(self.download_folder, file['title'])):
                os.makedirs(os.path.join(
                    self.download_folder, file['title']))
            self.delete_in_file_list(os.path.join(
                self.download_folder, file['title']))
            return

        must_download = True
        if os.path.exists(os.path.join(self.download_folder, file['title'])) and "md5Checksum" in file:
            md5 = self.md5(os.path.join(
                self.download_folder, file['title']))
            if md5 == file["md5Checksum"]:
                must_download = False
            print("{} alredy there, checking md5 are same? {} ('{}' vs '{}')".format(
                file['title'], not must_download, md5, file["md5Checksum"]))
            self.delete_in_file_list(os.path.join(
                self.download_folder, file['title']))

        if not os.path.exists(os.path.dirname(os.path.join(self.download_folder, file['title']))):
            os.makedirs(os.path.dirname(os.path.join(
                self.download_folder, file['title'])))

        if must_download is True:
            try:
                if file["mimeType"] not in self.mimetypes.keys() and int(file["fileSize"]) < 1000000:
                    file.GetContentFile(os.path.join(
                        self.download_folder, file['title']))
                else:
                    while len(self.threads) > 5:
                        for t in self.threads:
                            if t.is_alive() == False:
                                self.threads.remove(t)
                    print("there is currently {} threads alive".format(
                        len(self.threads)))
                    p = None
                    if file["mimeType"] not in self.mimetypes.keys():
                        p = Downloader(self.download_folder, file)
                    else:
                        p = Downloader(self.download_folder, file,
                                       self.mimetypes[file["mimeType"]])
                    print("Waking up new thread")
                    p.start()
                    self.threads.append(p)
                    self.delete_in_file_list(os.path.join(
                        self.download_folder, file['title']))

            except Exception as e:
                print("Error on : {}".format(file['title']))
                print(e)
                self.error_files.append(file['title'])
        del file

    def delete_in_file_list(self, path):
        if path in self.current_files:
            del self.current_files[path]

    def delete_file_path(self, obj):
        if obj["is_file"] is True:
            if os.path.exists(obj["path"]):
                os.remove(obj["path"])
        else:
            if os.path.exists(obj["path"]):
                shutil.rmtree(obj["path"])

    def __init__(self, file_path, file_config="/etc/pydrivesync.yaml", gdriveIds=["root"]):
        self.download_folder = os.path.join(
            os.path.abspath(os.getcwd()), file_path, self.DRIVE_PATH)
        if not os.path.exists(self.download_folder):
            os.mkdir(self.download_folder)
        gauth = GoogleAuth(settings_file=file_config)
        gauth.CommandLineAuth()
        self.drive = GoogleDrive(gauth)
        self.gdriveIds = gdriveIds

    def run(self):
        self.list_all_files(self.download_folder)
        for gdrive_path in self.gdriveIds:
            self.list_all_files_google(gdrive_path)

        for files_local in self.current_files.keys():
            print("Deleting : {}".format(files_local))
            self.delete_file_path(self.current_files[files_local])

        while len(self.threads) != 0:
            for t in self.threads:
                if t.is_alive() == False:
                    self.threads.remove(t)


def copyConfigFile(config_file):
    if config_file is not None:
        if not os.path.exists(config_file):
            shutil.copyfile(pkg_resources.resource_filename(
                __name__, "pydrivesync.yaml"), config_file)


def run():
    import sys
    import argparse
    version_str = 'PyDriveSync v{}'.format(constance.__VERSION__)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path", help="path is the path that will be used to sync data", type=str)
    parser.add_argument(
        "-c", "--config", help="path to config yaml file, default /etc/pydrivesync.yaml")
    parser.add_argument("--gdriveIds", "-g",
                        help="gdriveIds to specifie root folders ex : pathId1,pathId2,pathId3...")
    parser.add_argument('--version', action='version', version=version_str)
    args = parser.parse_args()
    gdriveIds = ["root"]
    if args.config:
        config_file = args.config
    else:
        config_file = "/etc/pydrivesync.yaml"
        copyConfigFile("/etc/pydrivesync.yaml")
    if args.gdriveIds:
        gdriveIds = args.gdriveIds.split(",")
    p = PyDriveSync(args.path, config_file, gdriveIds)
    p.run()
    print(p.error_files)
