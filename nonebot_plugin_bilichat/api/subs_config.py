import nonebot
from nonebot.compat import model_dump
from nonebot.log import logger
from nonebot_plugin_auto_bot_selector.target import SupportedPlatform
from pydantic import ValidationError

from ..model.api import FaildResponse, Response
from ..model.api.subs_config import Subs, UpdateUserSubConfig, UserSubConfig
from ..subscribe.manager import SubscriptionSystem
from .base import app

config = nonebot.get_driver().config


@app.get("/api/subs_config")
async def get_subs() -> Response[Subs]:
    return Response[Subs](data=Subs(**SubscriptionSystem.dump_dict()))


@app.put("/api/subs_config")
async def update_subs(data: Subs) -> Response[Subs] | FaildResponse:
    try:
        # 不接收来自前端的 uploaders，由后端自行推导并校验
        await SubscriptionSystem.load(
            model_dump(
                data,
                exclude={
                    "uploaders",
                },
            )
        )
        return Response[Subs](data=Subs(**SubscriptionSystem.dump_dict()))
    except (ValueError, ValidationError) as e:
        return FaildResponse(code=422, message=str(e))
    except Exception as e:
        logger.exception(e)
        return FaildResponse(code=400, message=str(e))


@app.patch("/api/subs_config/users/{platform}/{user_id}/subscriptions/{uid}")
async def update_user_subscription(
    platform: str,
    user_id: str,
    uid: int,
    data: UpdateUserSubConfig,
) -> Response[UserSubConfig] | FaildResponse:
    """更新指定推送目标的单个 UP 主订阅开关。"""
    user_key = f"{platform}-_-{user_id}"
    user = SubscriptionSystem.users.get(user_key)
    if user is None:
        return FaildResponse(code=404, message="订阅目标不存在")

    subscription = user.subscriptions.get(uid)
    if subscription is None:
        return FaildResponse(code=404, message="订阅不存在")

    subscription.dynamic = data.dynamic
    subscription.dynamic_at_all = data.dynamic_at_all
    subscription.live = data.live
    subscription.live_at_all = data.live_at_all
    subscription.live_close = data.live_close
    SubscriptionSystem.save_to_file()
    return Response[UserSubConfig](data=UserSubConfig(**subscription.dict()))


@app.get("/api/subs_config/platform")
async def get_supported_platform() -> Response[list[dict[str, str]]]:
    return Response[list[dict[str, str]]](
        data=[
            {
                "value": SupportedPlatform.qq_group,
                "label": "QQ群",
            },
            {
                "value": SupportedPlatform.qq_guild_channel,
                "label": "QQ频道",
            },
            {
                "value": SupportedPlatform.qq_private,
                "label": "QQ私聊",
            },
        ]
    )
