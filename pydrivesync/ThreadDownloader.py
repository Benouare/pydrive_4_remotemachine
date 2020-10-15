import os
import threading
import time

from pydrivesync.helper import sizeof_fmt


class Downloader(threading.Thread):

    file = None
    force_mime = None
    target_path = None

    def __init__(self, target_path, file, force_mime=None):
        threading.Thread.__init__(self)
        self.force_mime = force_mime
        self.file = file
        self.target_path = target_path

    def run(self):
        # print("Downloading with th{}".format(threading.get_ident()))
        start_time = time.time()
        self.file.GetContentFile(os.path.join(
            self.target_path, self.file['title']), self.force_mime)
        print("Downloaded  :: {} ({}) in {:.2f}s with th{}".format(
            self.file['title'], sizeof_fmt(self.file), (time.time() - start_time), threading.get_ident()))
