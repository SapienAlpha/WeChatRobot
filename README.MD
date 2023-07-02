# WeChatRobot
一个基于 [WeChatFerry](https://github.com/lich0821/WeChatFerry) 的微信机器人示例。

|[📖 文档](https://wechatferry.readthedocs.io/)|[📺 视频教程](https://mp.weixin.qq.com/s/APdjGyZ2hllXxyG_sNCfXQ)|
|:-:|:-:|

![Demo](demo.gif)

## Quick Start
0. 安装 Python，例如 [3.10.11](https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe)
1. 安装微信 `3.7.0.30`；安装文件在C:\Program Files(X86)\Tencent。如果微信被自动升级，需要卸载重新安装。
2. 克隆项目；克隆目录：C:\WeChatRobot-parent\WeChatRobot
```sh
git clone git@github.com:SapienAlpha/WeChatRobot.git
```

3. 安装依赖
```sh
# 升级 pip
python -m pip install -U pip
# 安装必要依赖
pip install -r requirements.txt
```

4. 运行。
切换到目录：C:\WeChatRobot-parent\WeChatRobot
直接运行程序会自动拉起微信：
```sh
python main.py
# 如果微信未打开，会自动打开微信；如果版本不对，也会有提示。
```

### 修改配置
配置文件 `config.yaml` 是运行程序后自动从模板复制过来的。

* 信号变更时的通知群，需要添加相应的 `roomId`(群里发送`?wxid`，机器人会将roomId发送到群里)：
```yaml
notifyGroups: [] # 信号变更时的通知群 roomId，大概长这样：2xxxxxxxxx3@chatroom
```

配置文件 `strategy_config.yaml`配置策略相关信息。