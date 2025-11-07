import os
from dataclasses import dataclass
from django.conf import settings
from .exceptions import PayHeroConfigurationError


@dataclass(frozen=True)
class PayHeroSettings:
    base_url: str
    api_key: str | None
    api_secret: str | None
    webhook_secret: str | None
    global_bearer_token: str | None
    timeout: int = 30

    @staticmethod
    def load() -> "PayHeroSettings":
        # Prefer Django settings, fallback to environment
        base_url = getattr(settings, "PAYHERO_BASE_URL", None) or os.getenv("PAYHERO_BASE_URL")
        api_key = getattr(settings, "PAYHERO_API_KEY", None) or os.getenv("PAYHERO_API_KEY")
        api_secret = getattr(settings, "PAYHERO_API_SECRET", None) or os.getenv("PAYHERO_API_SECRET")
        webhook_secret = getattr(settings, "PAYHERO_WEBHOOK_SECRET", None) or os.getenv("PAYHERO_WEBHOOK_SECRET")
        global_bearer_token = getattr(settings, "PAYHERO_GLOBAL_BEARER_TOKEN", None) or os.getenv("PAYHERO_GLOBAL_BEARER_TOKEN")
        timeout = int(getattr(settings, "PAYHERO_TIMEOUT", os.getenv("PAYHERO_TIMEOUT", 30)))

        if not base_url:
            raise PayHeroConfigurationError("PAYHERO_BASE_URL is required")
        # API credentials may be optional depending on auth scheme; don't guess.
        return PayHeroSettings(
            base_url=base_url,
            api_key=api_key,
            api_secret=api_secret,
            webhook_secret=webhook_secret,
            global_bearer_token=global_bearer_token,
            timeout=timeout,
        )
