from nonebot import require
from nonebot.plugin import PluginMetadata

from .config import Config, __version__

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_alconna")
require("nonebot_plugin_auto_bot_selector")
require("nonebot_plugin_waiter")


__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-bilichat",
    description="多种B站链接解析，视频词云，AI总结，你想要的都在 bilichat",
    usage="视频、专栏、动态解析直接发送链接、小程序、xml卡片即可，指令请参考 https://github.com/Well2333/nonebot-plugin-bilichat",
    homepage="https://github.com/Well2333/nonebot-plugin-bilichat",
    type="application",
    config=Config,
    supported_adapters={"~onebot.v11", "~onebot.v12", "~qq"},
    extra={
        "author": "djkcyl & Well404",
        "version": __version__,
        "priority": 1,
        "export": True,
    },
)

from . import api, base_content_parsing, commands  # noqa: F401, E402
