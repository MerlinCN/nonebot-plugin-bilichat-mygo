from nonebot_plugin_auto_bot_selector.target import SupportedPlatform
from pydantic import BaseModel, Field

SUBS_CONFIG_NAME_MAPPING = {
    "subs_limit": "全局订阅数量限制",
    "dynamic_interval": "动态轮询间隔",
    "live_interval": "直播轮询间隔",
    "push_delay": "每条推送的延迟",
    "dynamic_method": "动态推送方式",
    "rss_base": "动态RSS源",
    "rss_key": "动态RSS密钥",
}

SUBS_CONFIG_NAME_MAPPING_REVERSE = {v: k for k, v in SUBS_CONFIG_NAME_MAPPING.items()}


class SubsConfig(BaseModel):
    subs_limit: int = Field(5, ge=0, le=50)
    dynamic_interval: int = Field(90, ge=10)
    live_interval: int = Field(30, ge=10)
    push_delay: int = Field(3, ge=0)
    dynamic_method: str = "rest"
    rss_base: str = ""
    rss_key: str = ""


class UserSubConfig(BaseModel):
    """用户单个 UP 主订阅配置。"""

    uid: int = Field(..., title="UP 主 UID")
    dynamic: bool = Field(True, title="动态推送")
    dynamic_at_all: bool = Field(False, title="动态 @全体")
    live: bool = Field(True, title="直播推送")
    live_at_all: bool = Field(False, title="直播 @全体")
    live_close: bool = Field(False, title="下播提醒")
    live_notified_date: str = Field("", title="最近一次直播开播通知日期")


class UpdateUserSubConfig(BaseModel):
    """更新用户单个 UP 主订阅开关。"""

    dynamic: bool = Field(..., title="动态推送")
    dynamic_at_all: bool = Field(..., title="动态 @全体")
    live: bool = Field(..., title="直播推送")
    live_at_all: bool = Field(..., title="直播 @全体")
    live_close: bool = Field(..., title="下播提醒")


class User(BaseModel):
    user_id: str
    platform: SupportedPlatform
    at_all: bool = False
    subscriptions: list[UserSubConfig]


class Uploader(BaseModel):
    uid: int
    nickname: str = ""


class Subs(BaseModel):
    config: SubsConfig
    uploaders: list[Uploader] = []
    users: list[User] = []
