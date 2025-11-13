import base64
import logging
from typing import Any, Dict, Optional

import requests
from ..config import PayHeroSettings
from ..exceptions import (
    PayHeroAPIError,
    PayHeroTimeoutError,
    PayHeroConnectionError,
)


class PayHeroApiClient:
    """Thin HTTP client wrapper for PayHero API (no guessing of endpoints).

    Methods provide generic request helpers. Actual business actions live in PaymentService.
    """

    def __init__(self, settings: Optional[PayHeroSettings] = None):
        self.settings = settings or PayHeroSettings.load()
        self.logger = logging.getLogger(__name__)

    def _basic_auth_header(self) -> Optional[str]:
        if self.settings.api_key and self.settings.api_secret:
            token = base64.b64encode(f"{self.settings.api_key}:{self.settings.api_secret}".encode()).decode()
            return f"Basic {token}"
        return None

    def _bearer_auth_header(self) -> Optional[str]:
        if self.settings.global_bearer_token:
            return f"Bearer {self.settings.global_bearer_token}"
        return None

    def _headers(self, *, use_basic: bool | None = None, use_bearer: bool | None = None, has_json: bool = False) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if has_json:
            headers["Content-Type"] = "application/json"
        # Select auth scheme explicitly
        if use_basic:
            auth = self._basic_auth_header()
            if auth:
                headers["Authorization"] = auth
        if use_bearer:
            auth = self._bearer_auth_header()
            if auth:
                headers["Authorization"] = auth
        return headers

    def request(self, method: str, path: str, *, params: Dict[str, Any] | None = None,
                json: Dict[str, Any] | None = None, basic: bool | None = None, bearer: bool | None = None) -> Dict[str, Any]:
        url = f"{self.settings.base_url.rstrip('/')}/{path.lstrip('/')}"
        try:
            resp = requests.request(
                method.upper(),
                url,
                headers=self._headers(use_basic=bool(basic), use_bearer=bool(bearer), has_json=bool(json is not None)),
                params=params,
                json=json,
                timeout=self.settings.timeout,
            )
        except requests.exceptions.Timeout as exc:
            self.logger.warning("PayHero timeout on %s %s: %s", method, url, exc)
            raise PayHeroTimeoutError("Upstream timeout", status_code=504) from exc
        except requests.exceptions.ConnectionError as exc:
            self.logger.error("PayHero connection error on %s %s: %s", method, url, exc)
            raise PayHeroConnectionError("Upstream connection error", status_code=502) from exc
        except requests.exceptions.RequestException as exc:
            self.logger.exception("PayHero request error on %s %s", method, url)
            raise PayHeroAPIError("Upstream request error", status_code=502) from exc

        if not resp.ok:
            # Try parse JSON error details
            parsed: Dict[str, Any] | None = None
            try:
                parsed = resp.json()
            except ValueError:
                parsed = None
            self.logger.info(
                "PayHero non-2xx response %s for %s %s: %s",
                resp.status_code,
                method,
                url,
                parsed if parsed is not None else resp.text,
            )
            raise PayHeroAPIError(
                message=f"PayHero API error {resp.status_code}",
                status_code=resp.status_code,
                raw_body=resp.text,
                data=parsed,
            )
        try:
            return resp.json()
        except ValueError as e:  # pragma: no cover
            self.logger.error("Invalid JSON from PayHero for %s %s: %s", method, url, e)
            raise PayHeroAPIError("Invalid JSON response", status_code=502, raw_body=resp.text)
