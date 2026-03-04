# proyecto/utils/middleware.py
from __future__ import annotations

from pathlib import Path
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from proyecto.utils.exception_logs import LogContext, write_exception_log


class AdminExceptionLoggingMiddleware(MiddlewareMixin):
    """
    Captura excepciones del request/response cycle vía process_exception (confiable en Admin).
    """

    def process_exception(self, request, exception):
        path = (getattr(request, "path", "") or "")

        # Solo Admin
        if "/admin/" not in path:
            return None

        # Ping para comprobar
        try:
            ping_dir = Path(settings.BASE_DIR) / "exception_logs"
            ping_dir.mkdir(parents=True, exist_ok=True)
            (ping_dir / "middleware_ping.txt").write_text(
                f"process_exception atrapo: {type(exception).__name__}\npath={path}\n",
                encoding="utf-8"
            )
        except Exception:
            # No rompas el flujo si no puede escribir
            return None

        # Determinar "módulo" desde la URL: /admin/<Modulo>/<model>/...
        parts = [p for p in path.split("/") if p]  # ["admin","Sucursales","sucursale","93","delete"]
        modulo = parts[1] if len(parts) > 1 else "admin"
        modelo = parts[2] if len(parts) > 2 else "unknown"
        

        try:
            write_exception_log(
                LogContext(
                    modulo=modulo,
                    request=request,
                    extra={"modelo": modelo,
                        "where": "middleware",
                        "path_parts": parts[:8],},
                ),
                exception,
            )
        except Exception:
            # Si el writer falla, no bloquees el admin
            pass

        return None