# proyecto/utils/middleware.py
from __future__ import annotations

from django.utils.deprecation import MiddlewareMixin
from proyecto.utils.exception_logs import LogContext, write_exception_log


class AdminExceptionLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        path = (getattr(request, "path", "") or "")

        if "/admin/" not in path:
            return None

        parts = [p for p in path.split("/") if p]

        app_label = parts[1] if len(parts) > 1 else "admin"
        model_name = parts[2] if len(parts) > 2 else None
        action = parts[3] if len(parts) > 3 else None

        # IMPORTANTE: no tocar request.user aquí
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")

        try:
            params = dict(request.POST.items()) if request.method == "POST" else dict(request.GET.items())
        except Exception:
            params = {}

        user_agent = request.META.get("HTTP_USER_AGENT")

        extra = {
            "app_label": app_label,
            "model": model_name,
            "action": action,
            "ip": ip,
            "path": path,
            "method": request.method,
            "params": params,
            "user_agent": user_agent,
            "where": "middleware.process_exception",
        }

        try:
            write_exception_log(
                LogContext(
                    modulo=app_label,
                    request=request,
                    extra=extra,
                ),
                exception,
            )
        except Exception:
            # nunca dejes que el logger rompa más
            pass

        return None