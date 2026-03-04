# proyecto/utils/exception_logs.py
from __future__ import annotations

import re
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional

from django.conf import settings

SAFE_REPLACEMENT = "***REDACTED***"

DEFAULT_SENSITIVE_KEYS = {
    "password", "password1", "password2",
    "token", "csrfmiddlewaretoken",
    "rtn", "telefono", "email",
}


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _safe_filename(name: str) -> str:
    name = (name or "").strip()
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name or "Modulo"


def _sanitize_mapping(data: Mapping[str, Any], sensitive_keys: set[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in data.items():
        k_str = str(k)
        if k_str.lower() in sensitive_keys:
            out[k_str] = SAFE_REPLACEMENT
        else:
            out[k_str] = str(v)[:2000]
    return out


@dataclass
class LogContext:
    modulo: str
    request: Optional[Any] = None
    extra: Optional[dict[str, Any]] = None
    sensitive_keys: Optional[set[str]] = None


def write_exception_log(ctx: LogContext, exc: BaseException) -> str:
    stamp = _stamp()
    modulo = _safe_filename(ctx.modulo)
    prefix = "Excepcion" 
    filename = _safe_filename(f"{prefix}-{modulo}-{stamp}") + ".log"
    base_dir = Path(getattr(settings, "EXCEPTION_LOG_DIR", Path(settings.BASE_DIR) / "exception_logs"))
    base_dir.mkdir(parents=True, exist_ok=True)

    path = base_dir / filename
    sensitive = ctx.sensitive_keys or DEFAULT_SENSITIVE_KEYS

    lines: list[str] = []
    lines.append(f"timestamp={stamp}")
    lines.append(f"modulo={ctx.modulo}")
    lines.append(f"exception_type={type(exc).__name__}")
    lines.append(f"exception_message={str(exc)}")
    lines.append("")

    req = ctx.request
    if req is not None:
        try:
            user = getattr(req, "user", None)
            lines.append(f"user={getattr(user, 'username', None) if user else None}")
            lines.append(f"path={getattr(req, 'path', None)}")
            lines.append(f"method={getattr(req, 'method', None)}")

            post = getattr(req, "POST", None)
            if post:
                try:
                    post_dict = dict(post.items())
                except Exception:
                    post_dict = {}
                lines.append(f"post={_sanitize_mapping(post_dict, sensitive)}")
        except Exception:
            pass
        lines.append("")

    if ctx.extra:
        try:
            lines.append(f"extra={_sanitize_mapping(ctx.extra, sensitive)}")
            lines.append("")
        except Exception:
            pass

    lines.append("traceback:")
    lines.append("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)