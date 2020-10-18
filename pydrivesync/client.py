import hashlib
import os
import random
import shutil

import pkg_resources
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from pydrivesync import constance
from pydrivesync.helper import sizeof_fmt
from pydrivesync.ThreadDownloader import Downloader


class PyDriveSync():

    DRIVE_PATH = "google_drive/"
    current_files = dict()
    current_remote_files = []
    big_files_threads = []
    small_files_threads = []
    list_md5 = list()
    list_file = list()
    temp_list_md5 = list()
    temp_list_file = list()
    drive = None
    number_file = 0
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
            md5 = hashlib.md5(file.read()).hexdigest()
        file.close()
        return md5

    def list_all_files(self, path):
        objects = os.listdir(path)
        for file in objects:
            path_name = os.path.join(path, file)
            current_file = {
                "path": path_name,
                "is_file": os.path.isfile(path_name)
            }
            self.current_files[current_file["path"]] = current_file
            if not current_file["is_file"]:
                self.list_all_files(os.path.join(path, file))
            else:
                if not path_name in self.temp_list_file:
                    self.list_file.append(path_name)
                    self.list_md5.append(self.md5(path_name))
                else:
                    index  = self.temp_list_file.index(path_name)
                    self.list_file.append(path_name)
                    self.list_md5.append(self.temp_list_md5[index])
                self.number_file+=1
                if self.number_file == 1000:
                    self.update_file()

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

        random.shuffle(files)

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
        if file["mimeType"] == "application/vnd.google-apps.folder":
            if not os.path.exists(os.path.join(self.download_folder, file['title'])):
                os.makedirs(os.path.join(
                    self.download_folder, file['title']))
            self.delete_in_file_list(os.path.join(
                self.download_folder, file['title']))
            del file
            return

        must_download = True
        if os.path.join(self.download_folder, file['title']) in self.list_file and "md5Checksum" in file:
            id_item = self.list_file.index(os.path.join(self.download_folder, file['title']))
            if self.list_md5[id_item] == file["md5Checksum"]:
                must_download = False
            print("{} alredy there, checking md5 are same? {} ('{}' vs '{}')".format(
                file['title'], not must_download, self.list_md5[id_item], file["md5Checksum"]))
            self.delete_in_file_list(os.path.join(
                self.download_folder, file['title']))
            self.list_md5[id_item] = file["md5Checksum"]

        if not os.path.exists(os.path.dirname(os.path.join(self.download_folder, file['title']))):
            os.makedirs(os.path.dirname(os.path.join(
                self.download_folder, file['title'])))

        if must_download is True:
            try:
                if "md5Checksum" in file:
                    self.number_file+=1
                    self.list_md5.append(file["md5Checksum"])
                    self.list_file.append(os.path.join(self.download_folder, file['title']))
                if file["mimeType"] not in self.mimetypes.keys() and int(file["fileSize"]) < 10000000:
                    self.waking_up_thread_for(
                        file, self.small_files_threads, 7, "small")
                else:
                    self.waking_up_thread_for(
                        file, self.big_files_threads, 4, "big")
                print("###")
                print("Processing remote file {} ({}  {})".format(
                    file['title'], file["mimeType"], sizeof_fmt(file)))
                self.delete_in_file_list(os.path.join(
                    self.download_folder, file['title']))

            except Exception as e:
                print("Error on : {}".format(file['title']))
                print(e)
                self.error_files.append(file['title'])
        if (self.number_file==100):
            self.number_file=0
            self.update_file()
        del file

    def waking_up_thread_for(self, file, thread_list, limit, type):
        while len(thread_list) >= limit:
            for t in thread_list:
                if t.is_alive() == False:
                    thread_list.remove(t)
        print("there is currently {} threads alive for {} limit is {}".format(
            len(thread_list), type, limit))
        p = None
        if file["mimeType"] not in self.mimetypes.keys():
            p = Downloader(self.download_folder, file)
        else:
            p = Downloader(self.download_folder, file,
                           self.mimetypes[file["mimeType"]])
        print("Waking up new thread for '{}'".format(type))
        p.start()
        thread_list.append(p)

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
        temp_file_md5_list = pkg_resources.resource_filename(__name__, "temp_file_md5_list.txt")
        if os.path.exists(temp_file_md5_list):
            with open(temp_file_md5_list, 'r') as f:
                l = f.read()
                if l is not None and l !="":
                    line = l.split(":")
                    self.temp_list_file.append(line[0])
                    self.temp_list_md5.append(line[1])
            f.close()

    def update_file(self):
        temp_file_md5_list = pkg_resources.resource_filename(__name__, "temp_file_md5_list.txt")
        with open(temp_file_md5_list, 'w') as f:
            for i in range(len(self.list_file)):
                f.write('{}:{}\n'.format(self.list_file[i],self.list_md5[i]))
            f.close()

    def run(self):
        self.list_all_files(self.download_folder)
        self.temp_list_md5= list()
        self.temp_list_file = list()
        self.update_file()

        for gdrive_path in self.gdriveIds:
            self.list_all_files_google(gdrive_path)

        for files_local in self.current_files.keys():
            print("Deleting : {}".format(files_local))
            self.delete_file_path(self.current_files[files_local])

        threads = self.big_files_threads + self.small_files_threads
        while len(threads) != 0:
            for t in threads:
                if t.is_alive() == False:
                    threads.remove(t)
        self.update_file()


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
