class PayHeroError(Exception):
    """Base exception for PayHero integration."""


class PayHeroConfigurationError(PayHeroError):
    """Raised when mandatory configuration is missing."""


class PayHeroAPIError(PayHeroError):
    """Raised on non-2xx responses from PayHero API."""


class PayHeroSignatureError(PayHeroError):
    """Raised when webhook signature verification fails."""
