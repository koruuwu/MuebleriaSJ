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
    filename = _safe_filename(f"Excepcion-{modulo}-{stamp}") + ".log"

    base_dir = Path(getattr(settings, "EXCEPTION_LOG_DIR", Path(settings.BASE_DIR) / "exception_logs"))
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / filename

    sensitive = ctx.sensitive_keys or DEFAULT_SENSITIVE_KEYS
    fecha_legible = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    req = ctx.request
    username = "No disponible"
    ip = None
    url = None
    method = None
    params = {}

    if req is not None:
        try:
            # MUY IMPORTANTE: no fuerces request.user si la BD está caída
            raw_user = req.__dict__.get("user", None)
            if raw_user is not None:
                username = getattr(raw_user, "username", "No disponible")
        except Exception:
            username = "No disponible"

        try:
            xff = req.META.get("HTTP_X_FORWARDED_FOR")
            ip = xff.split(",")[0].strip() if xff else req.META.get("REMOTE_ADDR")
        except Exception:
            ip = "No disponible"

        try:
            url = getattr(req, "path", None)
        except Exception:
            url = "No disponible"

        try:
            method = getattr(req, "method", None)
        except Exception:
            method = "No disponible"

        try:
            if method == "POST":
                params = dict(getattr(req, "POST", {}).items())
            else:
                params = dict(getattr(req, "GET", {}).items())
        except Exception:
            params = {}

    params_safe = _sanitize_mapping(params, sensitive) if params else {}
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    lines: list[str] = []
    lines.append("ERROR REPORT")
    lines.append("--------------------------------")
    lines.append(f"Pantalla: {ctx.modulo}")
    lines.append(f"Fecha: {fecha_legible}")
    lines.append("")
    lines.append(f"Usuario: {username}")
    lines.append(f"IP: {ip}")
    lines.append(f"URL: {url}")
    lines.append(f"Metodo: {method}")
    lines.append("")
    lines.append("Parametros:")
    lines.append(str(params_safe))
    lines.append("")

    if ctx.extra:
        try:
            lines.append("Extra:")
            lines.append(str(_sanitize_mapping(ctx.extra, sensitive)))
            lines.append("")
        except Exception:
            pass

    lines.append("Traceback:")
    lines.append(tb)

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)