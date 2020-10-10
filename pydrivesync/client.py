from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
import hashlib
import shutil


class PyDriveSync():

    DRIVE_PATH = "google_drive/"
    current_files = dict()
    current_remote_files = []
    drive = None

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

    def list_all_files_google(self, id="root", name=None):
        files = self.drive.ListFile(
            {'q': "'{}' in parents and trashed=false".format(id)}).GetList()
        for file in files:
            if not id == "root":
                file["title"] = os.path.join(name, file["title"])
            if file["mimeType"] == "application/vnd.google-apps.folder":
                self.list_all_files_google(
                    "{}".format(file["id"]), file["title"])
        self.current_remote_files = self.current_remote_files + files

    def delete_file_path(self, obj):
        if obj["is_file"] is True:
            if os.path.exists(obj["path"]):
                os.remove(obj["path"])
        else:
            shutil.rmtree(obj["path"])

    def __init__(self, file_path, file_config="/etc/pydrivesync.yaml"):
        self.download_folder = os.path.join(
            os.path.abspath(os.getcwd()), file_path, self.DRIVE_PATH)
        gauth = GoogleAuth(settings_file=file_config)
        gauth.CommandLineAuth()
        self.drive = GoogleDrive(gauth)

    def run(self):
        if not os.path.exists(self.download_folder):
            os.mkdir(self.download_folder)
        self.list_all_files(self.download_folder)
        self.list_all_files_google()
        files_gdrive = [os.path.join(self.download_folder, x["title"])
                        for x in self.current_remote_files]
        for files_local in self.current_files.keys():
            if files_local not in files_gdrive:
                print("{} is missing in remote : deleting in local".format(files_local))
                self.delete_file_path(self.current_files[files_local])

        for file in self.current_remote_files:
            print("###")
            print("Processing remote file {} ({})".format(
                file['title'], file["mimeType"]))
            if file["mimeType"] == "application/vnd.google-apps.folder":
                if not os.path.exists(os.path.join(self.download_folder, file['title'])):
                    os.makedirs(os.path.join(
                        self.download_folder, file['title']))
            if file["mimeType"] not in ["application/vnd.google-apps.document", "application/vnd.google-apps.folder"]:
                must_download = True
                if os.path.join(self.download_folder, file['title']) in self.current_files.keys():
                    md5 = self.md5(os.path.join(
                        self.download_folder, file['title']))
                    if md5 == file["md5Checksum"]:
                        must_download = False
                    print("{} alredy there, checking md5 are same? {} ('{}' vs '{}')".format(
                        file['title'], not must_download, md5, file["md5Checksum"]))
                if must_download is True:
                    if not os.path.exists(os.path.dirname(os.path.join(self.download_folder, file['title']))):
                        os.makedirs(os.path.dirname(os.path.join(
                            self.download_folder, file['title'])))
                    file.GetContentFile(os.path.join(
                        self.download_folder, file['title']))
                    print("{} downloaded".format(file['title']))


def run():
    import sys
    if not len(sys.argv) == 2:
        print("pydrivesync folder")
        #print("pydrivesync configyaml")
        exit()
    path, config_file = sys.argv[1], sys.argv[2]
    p = PyDriveSync(path)
    p.run()
