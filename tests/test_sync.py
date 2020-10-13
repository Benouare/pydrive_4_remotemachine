import os
import unittest
from datetime import datetime, timedelta
from os import path

from pydrivesync.client import PyDriveSync, copyConfigFile


class pydrivesyncTest(unittest.TestCase):

    def test_read_file(self):
        p = PyDriveSync("tests/", "tests/test-settings.yaml")
        file = open("tests/google_drive/plop.text", "w")
        file.write("plop")
        file.close()

        file = open("tests/google_drive/plop2.txt", "w")
        file.write("plop")
        file.close()
        md5_1 = p.md5("tests/google_drive/plop2.txt")

        os.mkdir("tests/google_drive/test_folder")
        file = open("tests/google_drive/test_folder/plop3.txt", "w")
        file.write("diff")
        file.close()
        md5_2 = p.md5("tests/google_drive/test_folder/plop3.txt")

        p.run()
        self.assertTrue(os.path.exists("tests/google_drive/test_file.docx"))
        self.assertFalse(os.path.exists("tests/google_drive/plop.text"))
        self.assertTrue(os.path.exists("tests/google_drive/plop2.txt"))
        self.assertEqual(p.md5("tests/google_drive/plop2.txt"), md5_1)
        self.assertTrue(os.path.exists(
            "tests/google_drive/test_folder/plop3.txt"))
        self.assertNotEqual(
            p.md5("tests/google_drive/test_folder/plop3.txt"), md5_2)
        self.assertTrue(os.path.exists("tests/google_drive/Test_2folder/"))

    def test_config_file(self):
        copyConfigFile("tests/settings.yaml")
        self.assertTrue(os.path.exists("tests/settings.yaml"))
