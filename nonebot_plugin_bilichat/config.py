import importlib.util
import json
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from nonebot import get_driver, get_plugin_config, require
from nonebot.log import logger
from pydantic import BaseModel, Field, validator

from .lib.store import cache_dir

try:
    __version__ = version("nonebot_plugin_bilichat")
except Exception:
    __version__ = None


class Config(BaseModel):
    # general
    bilichat_block: bool = Field(default=False, title="阻塞其他的命令", json_schema_extra={"input_type": "boolean"})
    bilichat_enable_self: bool = Field(default=False, title="处理自身消息", json_schema_extra={"input_type": "boolean"})
    bilichat_only_self: bool = Field(default=False, title="仅处理自身消息", json_schema_extra={"input_type": "boolean"})
    bilichat_only_to_me: bool = Field(default=False, title="仅处理@消息", json_schema_extra={"input_type": "boolean"})
    bilichat_whitelist: list[str] = Field(default=[], title="白名单", json_schema_extra={"input_type": "stringArray"})
    bilichat_blacklist: list[str] = Field(default=[], title="黑名单", json_schema_extra={"input_type": "stringArray"})
    bilichat_cd_time: int = Field(default=120, title="冷却时间", json_schema_extra={"input_type": "number"})
    bilichat_neterror_retry: int = Field(
        default=3, title="网络错误重试次数", json_schema_extra={"input_type": "number"}
    )
    bilichat_show_error_msg: bool = Field(
        default=True, title="显示错误消息", json_schema_extra={"input_type": "boolean"}
    )
    bilichat_use_browser: bool = Field(
        default="Auto", title="使用浏览器渲染", json_schema_extra={"input_type": "boolean"}
    )
    bilichat_browser_shot_quality: int = Field(
        default=75, ge=10, le=100, title="浏览器截图质量", json_schema_extra={"input_type": "number"}
    )
    bilichat_cache_serive: Literal["json", "mongodb"] = Field(
        default="Auto", title="缓存服务", json_schema_extra={"input_type": "string"}
    )
    bilichat_text_fonts: str = Field(default="default", title="文本字体", json_schema_extra={"input_type": "string"})
    bilichat_emoji_fonts: str = Field(default="default", title="表情字体", json_schema_extra={"input_type": "string"})
    bilichat_webui_path: str | None = Field(
        default="bilichat", title="WebUI 路径", json_schema_extra={"input_type": "string"}
    )
    bilichat_subs_limit: int = Field(
        default=5, ge=0, le=50, title="订阅数量限制", json_schema_extra={"input_type": "number"}
    )
    bilichat_dynamic_interval: int = Field(
        default=90, ge=10, title="动态间隔时间", json_schema_extra={"input_type": "number"}
    )
    bilichat_live_interval: int = Field(
        default=30, ge=10, title="直播间隔时间", json_schema_extra={"input_type": "number"}
    )
    bilichat_push_delay: int = Field(default=3, ge=0, title="推送延迟时间", json_schema_extra={"input_type": "number"})
    bilichat_dynamic_method: Literal["rest", "grpc", "rss"] = Field(
        default="rest", title="动态获取方式", json_schema_extra={"input_type": "string"}
    )
    bilichat_rss_base: str = Field(default="", title="RSS 基础 URL", json_schema_extra={"input_type": "string"})
    bilichat_rss_key: str = Field(default="", title="RSS 密钥", json_schema_extra={"input_type": "string"})

    # command and subscribe
    bilichat_command_to_me: bool = Field(default=True, title="命令@我", json_schema_extra={"input_type": "boolean"})
    bilichat_cmd_start: str = Field(default="bilichat", title="命令前缀", json_schema_extra={"input_type": "string"})
    bilichat_cmd_add_sub: list[str] = Field(
        default=["订阅", "关注"], title="添加订阅命令", json_schema_extra={"input_type": "stringArray"}
    )
    bilichat_cmd_remove_sub: list[str] = Field(
        default=["退订", "取关"], title="删除订阅命令", json_schema_extra={"input_type": "stringArray"}
    )
    bilichat_cmd_check_sub: list[str] = Field(
        default=["查看", "查看订阅"], title="查看订阅命令", json_schema_extra={"input_type": "stringArray"}
    )
    bilichat_cmd_reset_sub: list[str] = Field(
        default=["重置", "重置配置"], title="重置订阅命令", json_schema_extra={"input_type": "stringArray"}
    )
    bilichat_cmd_at_all: list[str] = Field(
        default=["全体成员", "at全体"], title="全体成员命令", json_schema_extra={"input_type": "stringArray"}
    )
    bilichat_cmd_dynamic: list[str] = Field(
        default=["动态通知", "动态订阅"], title="动态通知命令", json_schema_extra={"input_type": "stringArray"}
    )
    bilichat_cmd_live: list[str] = Field(
        default=["直播通知", "直播订阅"], title="直播通知命令", json_schema_extra={"input_type": "stringArray"}
    )
    bilichat_cmd_checkdynamic: list[str] = Field(
        default=["查看动态"], title="查看动态命令", json_schema_extra={"input_type": "stringArray"}
    )
    bilichat_cmd_fetch: list[str] = Field(
        default=["获取内容", "解析内容"], title="获取内容命令", json_schema_extra={"input_type": "stringArray"}
    )
    bilichat_cmd_check_login: list[str] = Field(
        default=["查看登录账号"], title="查看登录账号命令", json_schema_extra={"input_type": "stringArray"}
    )
    bilichat_cmd_login_qrcode: list[str] = Field(
        default=["扫码登录"], title="扫码登录命令", json_schema_extra={"input_type": "stringArray"}
    )
    bilichat_cmd_logout: list[str] = Field(
        default=["登出账号"], title="登出账号命令", json_schema_extra={"input_type": "stringArray"}
    )
    bilichat_cmd_modify_cfg: list[str] = Field(
        default=["修改配置"], title="修改配置命令", json_schema_extra={"input_type": "stringArray"}
    )

    # basic info
    bilichat_basic_info: bool = Field(default=True, title="基础信息", json_schema_extra={"input_type": "boolean"})
    bilichat_basic_info_style: Literal["bbot_default", "style_blue"] = Field(
        default="Auto", title="基础信息样式", json_schema_extra={"input_type": "string"}
    )
    bilichat_basic_info_url: bool = Field(
        default=True, title="基础信息 URL", json_schema_extra={"input_type": "boolean"}
    )
    bilichat_reply_to_basic_info: bool = Field(
        default=True, title="回复基础信息", json_schema_extra={"input_type": "boolean"}
    )

    # dynamic
    bilichat_dynamic: bool = Field(default=True, title="动态", json_schema_extra={"input_type": "boolean"})
    bilichat_dynamic_style: Literal["dynamicrender", "browser_mobile", "browser_pc"] = Field(
        default="Auto", title="动态样式", json_schema_extra={"input_type": "string"}
    )
    bilichat_bilibili_cookie: str | None = Field(
        default=None, title="Bilibili Cookie", json_schema_extra={"input_type": "string"}
    )

    # both WC and AI
    bilichat_use_bcut_asr: bool = Field(
        default=True, title="使用 BCUT ASR", json_schema_extra={"input_type": "boolean"}
    )

    # Word Cloud
    bilichat_word_cloud: bool = Field(default=False, title="词云", json_schema_extra={"input_type": "boolean"})
    bilichat_word_cloud_size: list[int] = Field(
        default=[1000, 800], title="词云大小", json_schema_extra={"input_type": "numberArray"}
    )

    # AI Summary
    bilichat_summary_ignore_null: bool = Field(
        default=True, title="忽略空消息", json_schema_extra={"input_type": "boolean"}
    )
    bilichat_official_summary: bool = Field(
        default=False, title="官方摘要", json_schema_extra={"input_type": "boolean"}
    )
    bilichat_openai_token: str | None = Field(
        default=None, title="OpenAI Token", json_schema_extra={"input_type": "string"}
    )
    bilichat_openai_proxy: str | None = Field(
        default=None, title="OpenAI Proxy", json_schema_extra={"input_type": "string"}
    )
    bilichat_openai_model: Literal["gpt-4o", "gpt-4o-mini"] = Field(
        default="gpt-4o", title="OpenAI 模型", json_schema_extra={"input_type": "string"}
    )
    bilichat_openai_token_limit: int = Field(
        default=3500, title="OpenAI Token 限制", json_schema_extra={"input_type": "number"}
    )
    bilichat_openai_api_base: str = Field(
        default="https://api.openai.com", title="OpenAI API Base", json_schema_extra={"input_type": "string"}
    )

    @validator("bilichat_cache_serive", always=True, pre=True)
    def check_cache_serive(cls, v):
        if v == "json":
            return v
        try:
            if not importlib.util.find_spec("nonebot_plugin_mongodb"):
                raise ImportError
            require("nonebot_plugin_mongodb")
            if v == "Auto":
                logger.info("bilichat_cache_serive 可以使用 MongoDB 作为缓存服务")
            return "mongodb"
        except Exception as e:
            if v == "Auto":
                logger.info("bilichat_cache_serive 无法使用 MongoDB 作为缓存服务, 使用 JSON 文件作为缓存服务")
                return "json"
            raise RuntimeError(
                "未安装 MongoDB 所需依赖, 使用 **pip install nonebot-plugin-bilichat[all]** 来安装所需依赖"
            ) from e

    @validator("bilichat_use_browser", always=True, pre=True)
    def check_htmlrender(cls, v):
        if not v:
            return v
        try:
            require("nonebot_plugin_htmlrender")
            if v == "Auto":
                logger.info("bilichat_use_browser 所需依赖已安装，采用浏览器渲染模式")
            return True
        except Exception as e:
            if v == "Auto":
                logger.info("bilichat_use_browser 所需依赖未安装，采用绘图渲染模式")
                return False
            raise RuntimeError(
                "浏览器渲染依赖未安装, 请选择其他渲染模式或使用 **pip install nonebot-plugin-bilichat[all]** 来安装所需依赖"
            ) from e

    @validator("bilichat_basic_info_style", always=True, pre=True)
    def check_use_browser_basic(cls, v, values):
        if v == "bbot_default":
            return v
        # 不包含浏览器
        if values["bilichat_use_browser"] is not True:
            if v == "Auto":
                return "bbot_default"
            raise RuntimeError(
                f"样式 {v} 需要浏览器渲染, 请开启 **bilichat_use_browser** 或设置 bilichat_basic_info_style 为 Auto"
            )
        # 包含浏览器
        return "style_blue" if v == "Auto" else v

    @validator("bilichat_dynamic_style", always=True, pre=True)
    def check_use_browser_dynamic(cls, v, values):
        if v == "dynamicrender":
            return v
        # 不包含浏览器
        if values["bilichat_use_browser"] is not True:
            if v == "Auto":
                return "dynamicrender"
            raise RuntimeError(
                f"样式 {v} 需要浏览器渲染, 请开启 **bilichat_use_browser** 或设置 bilichat_dynamic_style 为 Auto"
            )
        # 包含浏览器
        return "browser_mobile" if v == "Auto" else v

    @validator("bilichat_bilibili_cookie", always=True)
    def check_bilibili_cookie(cls, v):
        if not v:
            return v
        # verify cookie file
        if Path(v).is_file():
            try:
                json.loads(Path(v).read_text("utf-8"))
            except Exception as e:
                raise ValueError(f"无法读取 bilichat_bilibili_cookie: {v}") from e

        elif Path(v).is_dir():
            raise ValueError(f"bilichat_browser_cookie 需要一个文件, 而 {v} 是一个文件夹")

        elif v == "api":
            cookie_file = cache_dir.joinpath("bilibili_browser_cookies.json").absolute()
            cookie_file.touch(0o755)
            logger.info(f"在 {cookie_file.as_posix()} 创建 bilichat_bilibili_cookie 文件")
            return cookie_file.as_posix()

        else:
            raise ValueError(f"路径 {v} 无法识别")

        return v

    @validator("bilichat_openai_proxy", always=True, pre=True)
    def check_openai_proxy(cls, v, values):
        if not values["bilichat_openai_token"]:
            return v
        if v is None:
            logger.warning("你设置了 bilichat_openai_token 但未设置 bilichat_openai_proxy ，这可能会导致请求失败.")
        return v

    @validator("bilichat_openai_token_limit")
    def check_token_limit(cls, v, values):
        if values["bilichat_openai_token"] is None:
            return v
        if not isinstance(v, int):
            v = int(v)
        model: str = values["bilichat_openai_model"]
        if model.startswith("gpt-3.5"):
            max_limit = 15000 if "16k" in model else 3500
        elif model.startswith("gpt-4"):
            max_limit = 32200 if "32k" in model else 7600
        else:
            max_limit = 3500
        if v > max_limit:
            logger.error(f"模型 {model} 的 token 上限为 {max_limit} 而不是 {v}, token 将被重置为 {max_limit}")
            v = max_limit
        return v

    @validator("bilichat_openai_token", always=True)
    def check_pypackage_openai(cls, v):
        if importlib.util.find_spec("tiktoken") or not v:
            return v
        else:
            raise RuntimeError(
                "openai 依赖未安装, 使用 **pip install nonebot-plugin-bilichat[summary]** 来安装所需依赖"
            )

    @validator("bilichat_word_cloud", always=True)
    def check_pypackage_wordcloud(cls, v):
        if (importlib.util.find_spec("wordcloud") and importlib.util.find_spec("jieba")) or not v:
            return v
        else:
            raise RuntimeError(
                "wordcloud 依赖未安装, 使用 **pip install nonebot-plugin-bilichat[wordcloud]** 来安装所需依赖"
            )

    @validator("bilichat_webui_path", always=True)
    def check_api(cls, v: str):
        if not v:
            return v
        v = v.strip("/")
        if "/" in v:
            raise ValueError("bilichat_webui_path 不应包含 '/'")
        return v

    def verify_permission(self, uid: str | int) -> bool:
        if self.bilichat_whitelist:
            return str(uid) in self.bilichat_whitelist
        elif self.bilichat_blacklist:
            return str(uid) not in self.bilichat_blacklist
        else:
            return True


raw_config = get_driver().config
plugin_config = get_plugin_config(Config)
