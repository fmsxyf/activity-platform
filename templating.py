"""Jinja2 模板引擎配置"""

from fastapi.templating import Jinja2Templates

from flash import get_flashed_messages

templates = Jinja2Templates(directory="templates")
templates.env.globals["get_flashed_messages"] = get_flashed_messages
