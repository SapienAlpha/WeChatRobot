import logging

import yaml
import os
import shutil

class NotifyStatus(object):
    def __init__(self) -> None:
        self.reload()
        self.LOG = logging.getLogger("NotifyStatus")

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
        if yconfig==None:
            yconfig={}
        self.NOTIFY_STATUS=yconfig

    def save(self, notifyStatus: dict) -> None:
        pwd = os.path.dirname(os.path.abspath(__file__))
        try:
            with open(f"{pwd}/notify_status.yaml", "w") as fp:
                fp.write(yaml.dump(notifyStatus))
                fp.close()
        except BaseException as e:
            self.LOG.error(f"保存notify_status.yaml時失败：{e}")
            shutil.copyfile(f"{pwd}/notify_status_template.yaml", f"{pwd}/notify_status.yaml")
            with open(f"{pwd}/notify_status.yaml", "w") as fp:
                fp.write(yaml.dump(notifyStatus))
                fp.close()
