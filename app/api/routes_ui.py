from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

from app.config import get_settings

router = APIRouter(tags=["ui"])

WEB_DIR = Path(__file__).resolve().parents[1] / "web"

_DEV_ENVS = {"development", "dev", "local", "test"}

# The test chat page (with the demo login) exists for development only. Anywhere else the same address shows a
# short notice: the real assistant is used from inside Autorocket (the chat widget calls /api/v1/chat/stream).
_NOTICE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Autorocket Guide</title></head>
<body style="margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:system-ui,sans-serif;background:#f6f7fb;padding:24px">
<div style="max-width:420px;text-align:center;background:#fff;border-radius:16px;padding:32px;box-shadow:0 4px 24px rgba(0,0,0,.08)">
<div style="font-weight:700;font-size:20px;margin-bottom:8px">Please sign in</div>
<p style="color:#555;line-height:1.5;margin:0 0 20px">The Autorocket Guide opens from inside Autorocket. Please sign in there and use the chat assistant.</p>
<a href="https://autorocket.in" style="display:inline-block;background:#4f46e5;color:#fff;text-decoration:none;padding:10px 20px;border-radius:10px;font-weight:600">Go to Autorocket</a>
</div></div></body></html>"""


def _is_dev() -> bool:
    return get_settings().app_env.lower() in _DEV_ENVS


def _page():
    return FileResponse(WEB_DIR / "index.html") if _is_dev() else HTMLResponse(_NOTICE)


@router.get("/", include_in_schema=False)
async def index():
    return _page()


@router.get("/login", include_in_schema=False)
async def login():
    return _page()
