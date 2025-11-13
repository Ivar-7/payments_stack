class PayHeroError(Exception):
    """Base exception for PayHero integration."""


class PayHeroConfigurationError(PayHeroError):
    """Raised when mandatory configuration is missing."""


class PayHeroAPIError(PayHeroError):
    """Raised on non-2xx responses from PayHero API.

    Provides access to status_code, raw_body and parsed_data (if JSON could be parsed).
    """

    def __init__(self, message: str, status_code: int | None = None, raw_body: str | None = None, data: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.raw_body = raw_body
        self.data = data or {}


class PayHeroSignatureError(PayHeroError):
    """Raised when webhook signature verification fails."""


class PayHeroTimeoutError(PayHeroAPIError):
    """Raised when the upstream request times out."""


class PayHeroConnectionError(PayHeroAPIError):
    """Raised when the upstream request cannot connect."""
