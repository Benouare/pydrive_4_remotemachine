from pydrivesync.client import PyDriveSync, run

if __name__ == "__main__":
    client = PyDriveSync("tests/", "settings.yaml", ["0AKoW1sgNKNR8Uk9PVA"])
    client.run()
    # run()
