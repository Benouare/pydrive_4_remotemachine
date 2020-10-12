from pydrivesync.client import PyDriveSync

if __name__ == "__main__":
    client = PyDriveSync("", "settings.yaml")
    client.run()
