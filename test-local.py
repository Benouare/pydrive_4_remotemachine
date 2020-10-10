from pydrivesync.client import PyDriveSync

if __name__ == "__main__":
    client = PyDriveSync("","tests/nas.conf")
    client.run()
    #client.main()
