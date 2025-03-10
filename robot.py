# -*- coding: utf-8 -*-

import logging
import re
import time
import xml.etree.ElementTree as ET

from wcferry import Wcf, WxMsg

from configuration import Config
from func_chatgpt import ChatGPT
from func_chengyu import cy
from func_news import News
from job_mgmt import Job
from notify_status import NotifyStatus
from strategy_config import StrategyConfig


class Robot(Job):
    """个性化自己的机器人
    """

    def __init__(self, config: Config, wcf: Wcf, strategyConfig: StrategyConfig,notifyStatus:NotifyStatus) -> None:
        self.wcf = wcf
        self.config = config
        self.strategyConfig = strategyConfig
        self.notifyStatus=notifyStatus
        self.LOG = logging.getLogger("Robot")
        self.wxid = self.wcf.get_self_wxid()
        self.allContacts = self.getAllContacts()
        self.chat = None
        chatgpt = self.config.CHATGPT
        if chatgpt:
            self.chat = ChatGPT(chatgpt.get("key"), chatgpt.get("api"), chatgpt.get("proxy"), chatgpt.get("prompt"))

    def toAt(self, msg: WxMsg) -> bool:
        """处理被 @ 消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        return self.toChitchat(msg)

    def toChengyu(self, msg: WxMsg) -> bool:
        """
        处理成语查询/接龙消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        status = False
        texts = re.findall(r"^([#|?|？])(.*)$", msg.content)
        # [('#', '天天向上')]
        if texts:
            flag = texts[0][0]
            text = texts[0][1]
            if flag == "#":  # 接龙
                if cy.isChengyu(text):
                    rsp = cy.getNext(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True
            elif flag in ["?", "？"]:  # 查词
                if cy.isChengyu(text):
                    rsp = cy.getMeaning(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True

        return status

    def toChitchat(self, msg: WxMsg) -> bool:
        """闲聊，接入 ChatGPT
        """
        if not self.chat:  # 没接 ChatGPT，固定回复
            rsp = "你@我干嘛？"
        else:  # 接了 ChatGPT，智能回复
            q = re.sub(r"@.*?[\u2005|\s]", "", msg.content).replace(" ", "")
            rsp = self.chat.get_answer(q, (msg.roomid if msg.from_group() else msg.sender))

        if rsp:
            if msg.from_group():
                self.sendTextMsg(rsp, msg.roomid, msg.sender)
            else:
                self.sendTextMsg(rsp, msg.sender)

            return True
        else:
            self.LOG.error(f"Can't get response from ChatGPT.")
            return False

    def processMsg(self, msg: WxMsg) -> None:
        """当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
        此处可进行自定义发送的内容,如通过 msg.content 关键字自动获取当前天气信息，并发送到对应的群组@发送者
        群号：msg.roomid  微信ID：msg.sender  消息内容：msg.content
        content = "xx天气信息为："
        receivers = msg.roomid
        self.sendTextMsg(content, receivers, msg.sender)
        """

        # 群聊消息
        if msg.from_group():
            self.processRequest(msg)
            return  # 处理完群聊信息，后面就不需要处理了

        if msg.type == 0x01:  # 文本消息
            # 让配置加载更灵活，自己可以更新配置。也可以利用定时任务更新。
            if msg.from_self():
                if msg.content == "UPDATE":
                    self.config.reload()
                    self.LOG.info("config updated")
            else:
                self.processRequest(msg)
            return

        # 非群聊信息，按消息类型进行处理
        if msg.type == 37:  # 好友请求
            self.autoAcceptFriendRequest(msg)

        elif msg.type == 10000:  # 系统信息
            self.sayHiToNewFriend(msg)

    def processRequest(self, msg: WxMsg) -> None:
        command = msg.content
        if msg.is_at(self.wxid):  # 被@
            command = re.sub(r"@.*?[\u2005|\s]", "", command).replace(" ", "")

        command = command.lower().strip()
        if '?help' == command:
            if msg.from_group():
                self.sendTextMsg(self.strategyConfig.HELP_REPLY, msg.roomid, msg.sender)
            else:
                self.sendTextMsg(self.strategyConfig.HELP_REPLY, msg.sender)
        elif command =="?wxid":
            if msg.from_group():
                self.sendTextMsg(msg.roomid, msg.roomid, msg.sender)
        elif command in self.strategyConfig.STRATEGY_CONFIG:
            strategyInfo = self.strategyConfig.STRATEGY_CONFIG[command]
            replyText = '最新的' + strategyInfo[
                'explanation'] + '。\r' + '策略仅供参考，不构成任何投资建议。请务必阅读免责声明(http://webapp.sapienalpha.net/)'
            chartPath = self.config.BASE_PATH + strategyInfo['chartFile']
            if msg.from_group():
                self.sendTextMsg(replyText, msg.roomid, msg.sender)
                self.sendImgMsg(chartPath, msg.roomid)
            else:
                self.sendTextMsg(replyText, msg.sender)
                self.sendImgMsg(chartPath,msg.sender)

    def onMsg(self, msg: WxMsg) -> int:
        try:
            self.LOG.debug(msg)  # 打印信息
            self.processMsg(msg)
        except Exception as e:
            self.LOG.error(e)

        return 0

    def enableRecvMsg(self) -> None:
        self.wcf.enable_recv_msg(self.onMsg)

    def sendTextMsg(self, msg: str, receiver: str, at_list: str = "") -> None:
        """ 发送消息
        :param msg: 消息字符串
        :param receiver: 接收人wxid或者群id
        :param at_list: 要@的wxid, @所有人的wxid为：nofity@all
        """
        # msg 中需要有 @ 名单中一样数量的 @
        ats = ""
        if at_list:
            wxids = at_list.split(",")
            for wxid in wxids:
                # 这里偷个懒，直接 @昵称。有必要的话可以通过 MicroMsg.db 里的 ChatRoom 表，解析群昵称
                ats += f" @{self.allContacts.get(wxid, '')}"

        # {msg}{ats} 表示要发送的消息内容后面紧跟@，例如 北京天气情况为：xxx @张三，微信规定需这样写，否则@不生效
        if ats == "":
            self.LOG.debug(f"To {receiver}: {msg}")
            self.wcf.send_text(f"{msg}", receiver, at_list)
        else:
            self.LOG.debug(f"To {receiver}: {ats}\r{msg}")
            self.wcf.send_text(f"{ats}\n\n{msg}", receiver, at_list)

    def sendImgMsg(self, path: str, receiver: str, at_list: str = "") -> None:
        """ 发送消息
        :param path: 图片路径
        :param receiver: 接收人wxid或者群id
        :param at_list: 要@的wxid, @所有人的wxid为：nofity@all
        """
        # {msg}{ats} 表示要发送的消息内容后面紧跟@，例如 北京天气情况为：xxx @张三，微信规定需这样写，否则@不生效
        self.LOG.debug(f"Send img To {receiver}: {path}")
        self.wcf.send_image(path, receiver)

    def getAllContacts(self) -> dict:
        """
        获取联系人（包括好友、公众号、服务号、群成员……）
        格式: {"wxid": "NickName"}
        """
        contacts = self.wcf.query_sql("MicroMsg.db", "SELECT UserName, NickName FROM Contact;")
        return {contact["UserName"]: contact["NickName"] for contact in contacts}

    def keepRunningAndBlockProcess(self) -> None:
        """
        保持机器人运行，不让进程退出
        """
        while True:
            self.runPendingJobs()
            time.sleep(1)

    def autoAcceptFriendRequest(self, msg: WxMsg) -> None:
        try:
            xml = ET.fromstring(msg.content)
            v3 = xml.attrib["encryptusername"]
            v4 = xml.attrib["ticket"]
            scene = xml.attrib["scene"]
            self.wcf.accept_new_friend(v3, v4, scene)

        except Exception as e:
            self.LOG.error(f"Error when agree friend request: {e}")

    def sayHiToNewFriend(self, msg: WxMsg) -> None:
        nickName = re.findall(r"你已添加了(.*)，现在可以开始聊天了。", msg.content)
        if nickName:
            # 添加了好友，更新好友列表
            self.allContacts[msg.sender] = nickName[0]
            self.sendTextMsg(f"Hi {nickName[0]}，我自动通过了你的好友请求。", msg.sender)

    def newsReport(self) -> None:
        receivers = self.config.NEWS
        if not receivers:
            return

        news = News().get_important_news()
        for r in receivers:
            self.sendTextMsg(news, r)

    def checkConfigAndNotifySignal(self)->None:
        try:
            self.config.reload()
            self.strategyConfig.reload()
            self.notifyStatus.reload()

            strategyConfig = self.strategyConfig.STRATEGY_CONFIG
            preNotifyStatus = self.notifyStatus.NOTIFY_STATUS
            currentNotifyStatus = {}

            for key, value in strategyConfig.items():
                try:
                    if value['enableNotify']:
                        statusFile = self.config.BASE_PATH + value['statusFile']
                        f = open(statusFile)
                        currentSignal = f.readline().strip()
                        f.close()
                        if key in preNotifyStatus:
                            preSignal = preNotifyStatus[key]
                            if currentSignal != preSignal:
                                notifyText = '最新的' + value[
                                    'explanation'] + '。\r' + '策略仅供参考，不构成任何投资建议。请务必阅读免责声明(http://webapp.sapienalpha.net/)'
                                chartPath = self.config.BASE_PATH + value['chartFile']
                                for groupId in self.config.NOTIFY_GROUPS:
                                    self.sendTextMsg(notifyText, groupId)
                                    self.sendImgMsg(chartPath, groupId)
                        currentNotifyStatus[key] = currentSignal
                except BaseException as e:
                    self.LOG.error(f"Error when check strategies: {e}")
            self.notifyStatus.save(currentNotifyStatus)
        except BaseException as e:
            self.LOG.error(f"Timed task error: {e}")