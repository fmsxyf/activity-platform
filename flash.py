"""Flash 消息工具（基于 Session）"""

from fastapi import Request


def flash(request: Request, message: str, category: str = "success") -> None:
    """向 Session 中添加一条 flash 消息"""
    flashes = request.session.get("_flashes", [])
    flashes.append((category, message))
    request.session["_flashes"] = flashes


def get_flashed_messages(request: Request) -> list[tuple[str, str]]:
    """从 Session 中获取并清除所有 flash 消息"""
    flashes: list[tuple[str, str]] = request.session.pop("_flashes", [])
    return flashes
