import asyncio
from datetime import date
from json import JSONDecodeError
from typing import Sequence

from bilireq.exceptions import ResponseCodeError
from bilireq.live import get_rooms_info_by_uids
from httpx import ConnectError, TransportError
from nonebot.log import logger

from ..lib.bilibili_request import get_b23_url, hc
from ..model.bilibili.live import LiveRoom
from ..model.exception import AbortError
from ..optional import capture_exception
from .manager import CONFIG_LOCK, SubscriptionSystem, Uploader, UserSubConfig


def should_push_live_start(sub_config: UserSubConfig, today: date) -> bool:
    """判断当前订阅是否应该发送开播通知。"""
    if not sub_config.live:
        return False
    if not sub_config.live_once_per_day:
        return True
    return not sub_config.has_live_notified_today(today)


async def push_live_start(up: Uploader, content: list[str | bytes]) -> None:
    """向订阅用户推送开播通知。"""
    today = date.today()
    notified = False
    for user in up.subscribed_users:
        sub_config = user.subscriptions[up.uid]
        if should_push_live_start(sub_config, today):
            await user.push_to_user(content=content, at_all=sub_config.live_at_all or user.at_all)
            sub_config.mark_live_notified_today(today)
            notified = True
    if notified:
        SubscriptionSystem.save_to_file()


async def push_live_close(up: Uploader, room: LiveRoom) -> None:
    """按配置向订阅用户推送下播通知。"""
    live_prompt = f"UP {room.uname}({room.uid}) 已下播"
    url = await get_b23_url(f"https://live.bilibili.com/{room.room_id}")
    content = [live_prompt, url]
    notified = False
    for user in up.subscribed_users:
        sub_config = user.subscriptions[up.uid]
        if sub_config.live_close:
            await user.push_to_user(content=content, at_all=sub_config.live_at_all or user.at_all)
            notified = True
    if not notified:
        logger.info(f"UP {room.uname}({room.uid}) 已下播，所有订阅配置均未开启下播通知")


async def fetch_live(ups: Sequence[int]):
    try:
        status_infos = await get_rooms_info_by_uids(list(ups))
    except (TransportError, ConnectError, JSONDecodeError, ResponseCodeError) as e:
        logger.error(f"[Live] 获取直播状态失败: {type(e)} {e}")
        raise AbortError("Live Abort")
    except RuntimeError as e:
        logger.error(f"[Live] 获取直播状态失败: {type(e)} {e}")
        if "The connection pool was closed while" not in str(e):
            capture_exception(e)
        raise AbortError("Live Abort")
    except Exception as e:  # noqa
        capture_exception(e)
        raise e

    if not status_infos:
        return

    for up_id, _data in status_infos.items():
        up = SubscriptionSystem.activate_uploaders.get(int(up_id))
        room = LiveRoom(**_data)
        if not up:
            # 如果没找到该UP，则跳过
            continue
        while CONFIG_LOCK.locked():
            await asyncio.sleep(0)
        async with CONFIG_LOCK:
            try:
                logger.debug(f"[Live] {up.nickname}({up.uid}) 直播状态: {room.live_status}")
                # 已开播
                if room.live_status == 1:
                    # 如果是 -1 则为第一次刷取，跳过后续推送部分
                    if up.living == -1:
                        up.living = room.live_time
                    # 如果记录值为 0 则是刚开播，开始开播推送
                    elif up.living == 0:
                        up.living = room.live_time
                        live_prompt = (
                            f"UP {room.uname}({room.uid})"
                            f"在 {room.area_v2_name} / {room.area_name} 区开播啦 \n"
                            f"标题：{room.title}"
                        )
                        url = await get_b23_url(f"https://live.bilibili.com/{room.room_id}")
                        try:
                            live_image = (await hc.get(room.cover_from_user)).content
                        except Exception:
                            live_image = "\n"
                        logger.info(f"{live_prompt}")
                        content = [live_prompt, live_image, url]
                        await push_live_start(up=up, content=content)
                    # 如果记录值大于 0 则是正在直播，不进行开播推送
                    else:
                        up.living = room.live_time
                # 未开播或轮播，且记录大于 0，则更新状态并按配置发送下播推送
                elif up.living > 0:
                    up.living = 0
                    await push_live_close(up=up, room=room)
            finally:
                # 如果是 -1 则更新为 0
                if up.living == -1:
                    up.living = 0
