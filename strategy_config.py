import yaml
import os
import shutil

class StrategyConfig(object):
    def __init__(self) -> None:
        self.reload()

    def _load_config(self) -> dict:
        pwd = os.path.dirname(os.path.abspath(__file__))
        try:
            with open(f"{pwd}/strategy_config.yaml", "rb") as fp:
                yconfig = yaml.safe_load(fp)
        except FileNotFoundError:
            shutil.copyfile(f"{pwd}/strategy_config_template.yaml", f"{pwd}/strategy_config.yaml")
            with open(f"{pwd}/strategy_config.yaml", "rb") as fp:
                yconfig = yaml.safe_load(fp)

        return yconfig

    def reload(self) -> None:
        yconfig = self._load_config()
        convertedConfig = {}
        for key, value in yconfig.items():
            lowerKey = str(key).lower().strip()
            convertedConfig[lowerKey] = value

        self.STRATEGY_CONFIG = convertedConfig

        tmpHelpReply = '您可以发送以下命令获取最新预测：\r'
        for key, value in convertedConfig.items():
            tmpHelpReply += key + '获取最新的' + value['explanation'] + '\r'

        self.HELP_REPLY=tmpHelpReply