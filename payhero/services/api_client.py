import base64
import requests
from typing import Any, Dict, Optional
from . import __all__  # noqa: F401  (placeholder to avoid unused warnings if needed)
from ..config import PayHeroSettings
from ..exceptions import PayHeroAPIError


class PayHeroApiClient:
    """Thin HTTP client wrapper for PayHero API (no guessing of endpoints).

    Methods provide generic request helpers. Actual business actions live in PaymentService.
    """

    def __init__(self, settings: Optional[PayHeroSettings] = None):
        self.settings = settings or PayHeroSettings.load()

    def _basic_auth_header(self) -> Optional[str]:
        if self.settings.api_key and self.settings.api_secret:
            token = base64.b64encode(f"{self.settings.api_key}:{self.settings.api_secret}".encode()).decode()
            return f"Basic {token}"
        return None

    def _bearer_auth_header(self) -> Optional[str]:
        if self.settings.global_bearer_token:
            return f"Bearer {self.settings.global_bearer_token}"
        return None

    def _headers(self, *, use_basic: bool | None = None, use_bearer: bool | None = None) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
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
        url = f"{self.settings.base_url.rstrip('/')}/{path.lstrip('/') }"
        resp = requests.request(
            method.upper(),
            url,
            headers=self._headers(use_basic=bool(basic), use_bearer=bool(bearer)),
            params=params,
            json=json,
            timeout=self.settings.timeout,
        )
        if not resp.ok:
            raise PayHeroAPIError(f"PayHero API error {resp.status_code}: {resp.text}")
        try:
            return resp.json()
        except ValueError as e:  # pragma: no cover
            raise PayHeroAPIError(f"Invalid JSON response: {e}")
