# proyecto/utils/admin_exception_mixin.py
from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest

from proyecto.utils.exception_logs import LogContext, write_exception_log


class ExceptionLoggingAdminMixin:
    """
    Captura excepciones en puntos típicos del admin y genera:
    Excepcion: Modulo-YYYYMMDD-HHmmSS.log
    con traceback completo.
    """

    # Si lo quieres fijo a mano: exception_module_name = "clientes"
    exception_module_name: str | None = None

    def _modulo(self) -> str:
        # "nombre del modulo": aquí uso el app_label del modelo (ej: "clientes")
        return self.exception_module_name or self.model._meta.app_label

    def _log_and_message(self, request: HttpRequest, exc: Exception, hook: str, extra: dict):
        path = write_exception_log(
            LogContext(modulo=self._modulo(), request=request, extra={"admin_hook": hook, **extra}),
            exc
        )
        messages.error(request, f"Ocurrió un error. Se registró log: {path}")

    def save_model(self, request: HttpRequest, obj, form, change: bool) -> None:
        try:
            return super().save_model(request, obj, form, change)
        except Exception as exc:
            self._log_and_message(request, exc, "save_model", {
                "model": self.model._meta.label,
                "change": change,
                "object": str(obj),
            })
            raise

    def delete_model(self, request: HttpRequest, obj) -> None:
        try:
            return super().delete_model(request, obj)
        except Exception as exc:
            self._log_and_message(request, exc, "delete_model", {
                "model": self.model._meta.label,
                "object": str(obj),
            })
            raise

    def delete_queryset(self, request: HttpRequest, queryset) -> None:
        try:
            return super().delete_queryset(request, queryset)
        except Exception as exc:
            self._log_and_message(request, exc, "delete_queryset", {
                "model": self.model._meta.label,
                "count": getattr(queryset, "count", lambda: None)(),
            })
            raise

    def response_change(self, request: HttpRequest, obj):
        try:
            return super().response_change(request, obj)
        except Exception as exc:
            self._log_and_message(request, exc, "response_change", {
                "model": self.model._meta.label,
                "object": str(obj),
            })
            raise

    def get_actions(self, request):
        actions = super().get_actions(request)
        wrapped = {}
        for name, (func, action_name, desc) in actions.items():
            wrapped[name] = (self._wrap_action(func, name), action_name, desc)
        return wrapped

    def _wrap_action(self, func, action_name: str):
        def _wrapped(modeladmin, request, queryset):
            try:
                return func(modeladmin, request, queryset)
            except Exception as exc:
                self._log_and_message(request, exc, "action", {
                    "action": action_name,
                    "model": self.model._meta.label,
                    "count": getattr(queryset, "count", lambda: None)(),
                })
                raise
        _wrapped.__name__ = getattr(func, "__name__", "_wrapped_action")
        _wrapped.short_description = getattr(func, "short_description", None)
        return _wrapped