#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import signal

from wcferry import Wcf

from configuration import Config
from notify_status import NotifyStatus
from robot import Robot
from strategy_config import StrategyConfig


def main():
    config = Config()
    strategyConfig = StrategyConfig()
    notifyStatus=NotifyStatus()
    wcf = Wcf(debug=False)

    def handler(sig, frame):
        wcf.cleanup()  # 退出前清理环境
        exit(0)

    signal.signal(signal.SIGINT, handler)

    robot = Robot(config, wcf, strategyConfig,notifyStatus)
    robot.LOG.info("----Starting Wechat Robot----")

    # 机器人启动发送测试消息
    robot.sendTextMsg("----Wechat Robot start success!", "filehelper")

    # 接收消息
    robot.enableRecvMsg()

    robot.onEveryMinutes(1,robot.checkConfigAndNotifySignal)

    # 让机器人一直跑
    robot.keepRunningAndBlockProcess()


if __name__ == "__main__":
    main()
