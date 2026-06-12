# AGENTS.md — nonebot-plugin-bilichat-mygo

NoneBot2 插件，用于 B 站视频/专栏/动态链接解析、词云生成、AI 摘要和 UP 主订阅推送。

## 项目概览

- **框架**: NoneBot2（FastAPI 驱动）+ OneBot v11 适配器
- **语言**: Python 3.12+
- **包管理**: PDM（构建后端）、uv（运行时推荐）
- **构建后端**: pdm-backend
- **代码风格**: Ruff（line-length 120，target py312）

## 构建 / 运行 / 测试命令

```bash
# 安装依赖（推荐用 uv）
uv sync
uv sync --extra all          # 安装全部可选依赖（词云、AI 摘要、MongoDB 等）

# 运行 Bot
uv run bot.py

# Lint（项目配置了 ruff）
uv run ruff check .
uv run ruff format --check .

# 格式化
uv run ruff format .

# 类型检查（项目未配置 mypy/pyright，但建议手动运行）
uv run pyright nonebot_plugin_bilichat/
```

**⚠️ 本项目无测试套件。** 没有 tests/ 目录，没有 pytest 配置。改动后依赖 lint + 手动验证。

## 项目结构

```
nonebot_plugin_bilichat/
├── __init__.py              # 插件入口，require 依赖插件、声明 PluginMetadata
├── config.py                # Config(BaseModel) + validator 链，所有配置项
├── base_content_parsing.py  # 核心消息处理：链接匹配 → 内容解析 → 响应
├── optional.py              # 可选依赖的 graceful fallback（如 sentry_sdk）
├── wordcloud.py             # 词云生成
├── api/                     # FastAPI WebUI 路由
├── commands/                # NoneBot 命令处理器（订阅管理、登录等）
├── content/                 # 内容模型（Video, Column, Dynamic）
├── lib/                     # 工具库
│   ├── bilibili_request/    # B 站 API 请求（gRPC + REST）
│   ├── cache/               # 缓存层（JSON / MongoDB）
│   ├── draw/                # 图片渲染（PIL / 浏览器截图）
│   └── ...                  # b23_extract, bcut_asr, fonts, store 等
├── model/                   # Pydantic 数据模型
│   ├── exception.py         # 自定义异常层级
│   ├── api/                 # API 请求/响应模型
│   └── bilibili/            # B 站业务模型
└── subscribe/               # 订阅系统（manager + 定时任务）
```

## 订阅直播配置约定

- 单个订阅项的 `UserSubConfig.live_once_per_day` 控制该推送目标是否对对应 UP 每天只发送一次开播通知。
- 单个订阅项的 `UserSubConfig.live_close` 控制该推送目标是否接收对应 UP 的下播通知。
- 单个订阅项的 `UserSubConfig.quiet_time_ranges` 控制该推送目标订阅该 UP 的多段静默时段，时间字符串格式为 `HH:mm`；支持跨天，`start == end` 视为全天静默。
- 单个订阅项的 `UserSubConfig.live_dedupe_minutes` 控制开播通知分钟级去重，默认 `0` 表示关闭；成功推送开播后写入 `live_last_push_at`。
- 静默时段作用于动态、开播、下播三类推送，命中后直接丢弃本次推送，不做延迟补发。
- 推送判断优先级：对应推送开关关闭则不推送 → 命中订阅项静默时段则不推送 → 开播再判断每天推送一次 → 开播再判断分钟级去重 → 实际推送成功后更新对应记录字段。

## 代码风格指南

### 通用规则

- 用 `uv run` 而不是 `python`，用 `uv pip` 而不是 `pip`
- 永远用中文回复用户。代码中的注释和日志消息使用中文
- 代码生成和修改后，**必须加上类型注释和 docstring**
- import 语句**必须写到文件最上面**（唯一例外：`nonebot.require()` 后的导入用 `# noqa: E402`）
- 代码尽量简洁，**防止多层嵌套**
- 行宽上限 120 字符（ruff 配置）

### Pydantic 模型

- **不要用裸 dict**，优先用 Pydantic BaseModel
- 如果实在需要字典，使用 TypedDict
- Pydantic 定义 BaseModel **一定要用 Field**
- 项目同时兼容 Pydantic V1/V2（通过 `nonebot.compat.PYDANTIC_V2` 判断）
- 配置类参考 `config.py` 中的 `Config` 类：每个字段用 `Field(default=..., title=..., json_schema_extra={...})`
- 使用 `@validator` 做字段校验（项目当前风格）

```python
# ✅ 正确
class MyModel(BaseModel):
    name: str = Field(default="", title="名称")
    count: int = Field(default=0, ge=0, title="数量")

# ❌ 错误
class MyModel(BaseModel):
    name: str = ""
    data: dict = {}  # 不要用裸 dict
```

### 错误处理

- try/catch 中，**尽量 catch 核心会出错的点**，而不是整个包裹
- **尽量不要多层 try/catch 包着**，可以拆分
- 业务异常使用 `model/exception.py` 中的异常类：
  - `AbortError` — 外部因素（风控等）导致的可恢复异常
  - `CaptchaAbortError` — 需要验证码
  - `NotFindAbortError` — 资源未找到
  - `ProssesError` — 处理时的环境错误
- 网络请求需要 retry 逻辑时，使用 `plugin_config.bilichat_neterror_retry` 控制重试次数

### 日志

- 使用 `nonebot.log.logger`（即 loguru），**不要用 `logging` 标准库**
- 日志消息用中文
- 调试信息用 `logger.debug()`，常规信息用 `logger.info()`，异常用 `logger.exception()`

### 异步模式

- 全部使用 `async/await`，网络请求用 `httpx.AsyncClient`
- 并发控制使用 `asyncio.Lock()`（参考 `base_content_parsing.py` 和 `subscribe/manager.py`）
- NoneBot 命令处理器中的锁通过 `Depends(check_lock)` 注入

### Import 风格

```python
# 1. 标准库
import asyncio
import json
from pathlib import Path
from typing import Literal

# 2. 第三方库
from nonebot import get_driver
from nonebot.log import logger
from pydantic import BaseModel, Field, validator

# 3. 本项目内部模块（相对导入）
from ..config import plugin_config
from ..model.exception import AbortError
```

- 内部模块使用**相对导入**（`from ..config import ...`）
- NoneBot 插件依赖通过 `require()` 声明后再导入，加 `# noqa: E402`
- 未使用的导入用 `# noqa: F401` 标记（见 `__init__.py`）

### 命名规范

- 文件名：`snake_case`
- 类名：`PascalCase`（如 `SubscriptionSystem`, `VideoImage`）
- 函数/变量：`snake_case`
- 配置项前缀：`bilichat_`（全部小写下划线）
- 常量：`UPPER_SNAKE_CASE`（如 `CONFIG_LOCK`, `SUBSCRIBE_FILE`）

### NoneBot 命令模式

```python
# 在 commands/ 下定义命令
from .base import bilichat  # CommandGroup 实例

bili_xxx = bilichat.command("xxx", permission=SUPERUSER, aliases=set(plugin_config.bilichat_cmd_xxx))

@bili_xxx.handle()
async def handler(msg: Message = CommandArg(), user: User = Depends(get_user), lock: Lock = Depends(check_lock)):
    async with lock:
        # 处理逻辑
        await bili_xxx.finish("完成")
```

### 可选依赖处理

参考 `optional.py` — 可选依赖用 try/except ImportError 做 graceful fallback：

```python
try:
    from some_optional import feature
except ImportError:
    logger.warning("some_optional 未安装")
    def feature():
        pass
```

## Git 规范

- 涉及到 git 的**危险操作请一定要询问用户**（force push、hard reset 等）
- 发布通过 GitHub Actions（`.github/workflows/python-publish.yml`）
- `.env`、`cookies.json`、`bot.py`、`logs/` 在 `.gitignore` 中，**绝不提交**

## 关键依赖

| 依赖 | 用途 |
|---|---|
| nonebot2[fastapi] | Bot 框架 + FastAPI 驱动 |
| nonebot-adapter-onebot | QQ 协议适配 |
| nonebot-plugin-alconna | 跨平台消息构建 |
| nonebot-plugin-apscheduler | 定时任务（订阅轮询） |
| nonebot-plugin-localstore | 本地文件存储路径管理 |
| bilireq | B 站 gRPC/REST API 封装 |
| httpx | 异步 HTTP 客户端 |
| pillow | 图片处理 |
| dynrender-skia-opt | 动态渲染（Skia） |
| pydantic | 数据模型和配置校验 |

## 修改后必做

- 添加或删除功能、大量修改后，**同步更新本文件（AGENTS.md）**
- 确保 `uv run ruff check .` 和 `uv run ruff format --check .` 通过
- 对修改的文件运行 LSP 诊断，确认无类型错误
