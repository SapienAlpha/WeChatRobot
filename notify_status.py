import yaml
import os
import shutil

class NotifyStatus(object):
    def __init__(self) -> None:
        self.reload()

    def _load_config(self) -> dict:
        pwd = os.path.dirname(os.path.abspath(__file__))
        try:
            with open(f"{pwd}/notify_status.yaml", "rb") as fp:
                yconfig = yaml.safe_load(fp)
        except FileNotFoundError:
            shutil.copyfile(f"{pwd}/notify_status_template.yaml", f"{pwd}/notify_status.yaml")
            with open(f"{pwd}/notify_status.yaml", "rb") as fp:
                yconfig = yaml.safe_load(fp)

        return yconfig

    def reload(self) -> None:
        yconfig = self._load_config()
        self.NOTIFY_STATUS=yconfig

    def save(self, notifyStatus: dict) -> None:
        pwd = os.path.dirname(os.path.abspath(__file__))
        try:
            with open(f"{pwd}/notify_status.yaml", "rb") as fp:
                fp.write(yaml.dump(notifyStatus))
                fp.close()
        except FileNotFoundError:
            shutil.copyfile(f"{pwd}/notify_status_template.yaml", f"{pwd}/notify_status.yaml")
            with open(f"{pwd}/notify_status.yaml", "rb") as fp:
                fp.write(yaml.dump(notifyStatus))
                fp.close()
