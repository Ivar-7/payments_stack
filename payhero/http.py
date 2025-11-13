import logging
from typing import Callable, Any, Optional
from rest_framework.response import Response

from .exceptions import (
    PayHeroAPIError,
    PayHeroConfigurationError,
    PayHeroTimeoutError,
    PayHeroConnectionError,
)

logger = logging.getLogger(__name__)


def error_payload(detail: str, *, code: Optional[str] = None, status_code: Optional[int] = None, upstream: Optional[dict] = None) -> dict:
    payload = {"detail": detail}
    if code:
        payload["code"] = code
    if status_code:
        payload["status_code"] = status_code
    if upstream:
        payload["error"] = upstream
    return payload


def handle_exception(exc: Exception) -> Response:
    if isinstance(exc, PayHeroTimeoutError):
        return Response(error_payload("Upstream timeout", code="TIMEOUT", status_code=504), status=504)
    if isinstance(exc, PayHeroConnectionError):
        return Response(error_payload("Upstream connection error", code="CONNECTION_ERROR", status_code=502), status=502)
    if isinstance(exc, PayHeroAPIError):
        code = None
        msg = str(exc)
        if getattr(exc, "data", None):
            code = exc.data.get("error_code") or exc.data.get("code")
            msg = exc.data.get("error_message") or exc.data.get("message") or msg
        sc = exc.status_code or 502
        return Response(error_payload(msg, code=code, status_code=sc, upstream=exc.data or {}), status=sc)
    if isinstance(exc, PayHeroConfigurationError):
        # Surface the specific config error message
        return Response(error_payload(str(exc) or "Server misconfiguration for PayHero", code="CONFIG_ERROR", status_code=500), status=500)
    logger.exception("Unhandled exception in PayHero view")
    return Response(error_payload("Unexpected server error", code="UNEXPECTED_ERROR", status_code=500), status=500)


def safe_call(fn: Callable[[], Any], *, status_code: Optional[int] = None) -> Response:
    try:
        result = fn()
        if status_code:
            return Response(result, status=status_code)
        return Response(result)
    except Exception as exc:  # noqa: BLE001
        return handle_exception(exc)
