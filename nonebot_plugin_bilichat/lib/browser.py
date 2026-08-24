from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager
from typing import Any

from nonebot.log import logger
from nonebot_plugin_htmlrender import get_default_application
from playwright.async_api import Page, Request, Route
from yarl import URL

from .bilibili_request.auth import AuthManager
from .fonts_provider import get_font_async
from .store import static_dir

FONT_MIME_TYPES: Mapping[str, str] = {
    "collection": "font/collection",
    "otf": "font/otf",
    "sfnt": "font/sfnt",
    "ttf": "font/ttf",
    "woff": "font/woff",
    "woff2": "font/woff2",
}


async def pw_font_injecter(route: Route, request: Request) -> None:
    """将页面字体请求映射到 Bilichat 的本地字体资源。"""
    url = URL(request.url)
    if not url.is_absolute():
        raise ValueError("字体地址不合法")

    font_name = url.query["name"]
    try:
        font_path = await get_font_async(font_name)
    except (ConnectionError, FileNotFoundError):
        logger.error(f"找不到字体 {font_name}")
        await route.fallback()
        return

    logger.debug(f"请求字体文件 {font_name}")
    await route.fulfill(
        path=font_path,
        content_type=FONT_MIME_TYPES.get(url.suffix),
    )


mobile_style_js = static_dir.joinpath("browser", "mobile_style.js")


@asynccontextmanager
async def get_new_page(
    device_scale_factor: float = 2,
    mobile_style: bool = False,
    **kwargs: Any,
) -> AsyncGenerator[Page]:
    """从 HTMLRender Playwright Provider 租用并初始化页面。"""
    if mobile_style:
        kwargs["user_agent"] = (
            "5.0 (Linux; Android 13; SM-A037U) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36  uacq"
        )
    playwright = get_default_application().extensions.playwright
    async with playwright.page(device_scale_factor=device_scale_factor, **kwargs) as page:
        if cookies := AuthManager.get_cookies():
            logger.debug("正在为浏览器添加cookies")
            await page.context.add_cookies(
                [
                    {
                        "domain": ".bilibili.com",
                        "name": name,
                        "path": "/",
                        "value": value,
                    }
                    for name, value in cookies.items()
                ]
            )
        yield page


async def network_request(request: Request) -> None:
    """记录已完成网络请求的状态和耗时。"""
    url = request.url
    method = request.method
    response = await request.response()
    if response:
        status = response.status
        timing = "%.2f" % response.request.timing["responseEnd"]
    else:
        status = "/"
        timing = "/"
    logger.debug(f"[Response] [{method} {status}] {timing}ms <<  {url}")


def network_requestfailed(request: Request) -> None:
    """记录失败网络请求的错误信息。"""
    url = request.url
    fail = request.failure
    method = request.method
    logger.warning(f"[RequestFailed] [{method} {fail}] << {url}")
