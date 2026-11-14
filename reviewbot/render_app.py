"""Inject a ledger (and optional audio) into the prebuilt single-file React review app.

The app is built once (ui/ → reviewbot/static/review-app.template.html); CI needs no Node.
Security: the ledger is inert JSON with '<' escaped (no </script> breakout); a CSP meta tag allows only the
exact inline script/style by sha256 hash, no network, data: URIs only for media/fonts/images.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path

TEMPLATE = Path(__file__).parent / "static" / "review-app.template.html"


def _sha(text: str) -> str:
    return "'sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode() + "'"


def _inert(obj) -> str:
    return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def available() -> bool:
    return TEMPLATE.exists()


def render(ledger: dict, audio_script: str = "", audio_file: Path | None = None) -> str:
    html = TEMPLATE.read_text(encoding="utf-8")
    scripts = re.findall(r'<script type="module"[^>]*>(.*?)</script>', html, re.S)
    styles = re.findall(r"<style[^>]*>(.*?)</style>", html, re.S)
    csp = ("default-src 'none'; img-src data:; font-src data:; media-src data:; connect-src 'none'; "
           f"script-src {' '.join(map(_sha, scripts))}; style-src {' '.join(map(_sha, styles))}; "
           "base-uri 'none'; form-action 'none'")
    src = None
    if audio_file and audio_file.exists():
        mime = {".m4a": "audio/mp4", ".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".opus": "audio/ogg", ".wav": "audio/wav"}.get(audio_file.suffix, "audio/mp4")
        src = f"data:{mime};base64," + base64.b64encode(audio_file.read_bytes()).decode()
    html = html.replace("<!--CSP-->", f'<meta http-equiv="Content-Security-Policy" content="{csp}">', 1)
    html = html.replace("__LEDGER__", _inert(ledger), 1)
    html = html.replace("__AUDIO__", _inert({"src": src, "script": audio_script}), 1)
    return html
