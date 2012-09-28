
class AllSettingsModel():
    def __init__(self, version_file="/usr/share/endlessm/version.txt"):
        self._version_file = version_file

    def get_current_version(self):
        version_text = "EndlessOS"

        with open(self._version_file, "r") as f:
            version_text = f.read()

        return version_text
