"""PayHero payment service.

Coordinates high-level operations across v2 (Basic auth) and Global (Bearer) endpoints.
Pure orchestration lives here; HTTP specifics are in PayHeroApiClient.
"""

from typing import Dict, Any, List, Optional
from django.db import transaction
from ..models import PayHeroTransaction
from .api_client import PayHeroApiClient
from ..exceptions import PayHeroConfigurationError

# v2 endpoint paths (Basic Auth)
SERVICE_WALLET_BALANCE_PATH = "api/v2/wallets"  # GET ?wallet_type=service_wallet
PAYMENT_CHANNEL_BALANCE_PATH = "api/v2/payment_channels/{channel_id}"  # GET
TOPUP_PATH = "api/v2/topup"  # POST
PAYMENTS_PATH = "api/v2/payments"  # POST initiate payment
WITHDRAW_PATH = "api/v2/withdraw"  # POST
TRANSACTIONS_PATH = "api/v2/transactions"  # GET pagination
TRANSACTION_STATUS_PATH = "api/v2/transaction-status"  # GET ?reference=xxx

# Global endpoints (Bearer Auth)
GLOBAL_DISCOVERY_PATH = "api/global/discovery/payment-world/"  # GET ?country=KE
GLOBAL_PAYMENTS_PATH = "api/global/payments"  # POST


class PaymentService:
    """Coordinates PayHero operations across v2 (Basic) and Global (Bearer) endpoints.

    This layer prepares payloads, triggers API calls through the client, and
    records minimal transaction state where applicable. It intentionally does
    not swallow upstream errors; those are handled at the API view layer for
    consistent HTTP responses.
    """

    def __init__(self, client: PayHeroApiClient | None = None):
        self.client = client or PayHeroApiClient()

    # ------------------ v2 (Basic) ------------------
    def get_service_wallet_balance(self) -> Dict[str, Any]:
        return self.client.request("GET", SERVICE_WALLET_BALANCE_PATH, params={"wallet_type": "service_wallet"}, basic=True)

    def get_payment_channel_balance(self, channel_id: Optional[int] = None) -> Dict[str, Any]:
        channel = channel_id if channel_id is not None else self.client.settings.default_channel_id
        if channel is None:
            raise PayHeroConfigurationError("Missing channel_id and PAYHERO_CHANNEL_ID not configured")
        path = PAYMENT_CHANNEL_BALANCE_PATH.format(channel_id=channel)
        return self.client.request("GET", path, basic=True)

    @transaction.atomic
    def topup_service_wallet(self, *, amount: int, phone_number: str, reference: str | None = None) -> Dict[str, Any]:
        payload = {"amount": amount, "phone_number": phone_number}
        resp = self.client.request("POST", TOPUP_PATH, json=payload, basic=True)
        # Record as transaction for internal traceability
        ref = reference or resp.get("reference") or resp.get("CheckoutRequestID")
        txn = PayHeroTransaction.objects.create(
            reference=ref,
            amount=amount,
            phone_number=phone_number,
            operation_type="topup",
            status=resp.get("status", PayHeroTransaction.Status.QUEUED),
            metadata={"topup_response": resp},
        )
        return {"reference": txn.reference, "status": txn.status, "raw": resp}

    @transaction.atomic
    def initiate_payment(self, *, amount: int, phone_number: str, channel_id: Optional[int] = None, provider: str,
                        reference: str | None = None, external_reference: str | None = None,
                        customer_name: str | None = None, callback_url: str | None = None,
                        credential_id: str | None = None, network_code: str | None = None) -> Dict[str, Any]:
        """Initiate a customer payment.

        Required: amount, phone_number, channel_id, provider.
        Optional metadata fields are passed through to the upstream API when provided.
        """
        # For payments, prefer an explicit payments_channel_id, then default
        settings = self.client.settings
        channel = channel_id if channel_id is not None else (settings.payments_channel_id or settings.default_channel_id)
        if channel is None:
            raise PayHeroConfigurationError("Missing channel_id and PAYHERO_CHANNEL_ID not configured")
        payload: Dict[str, Any] = {
            "amount": amount,
            "phone_number": phone_number,
            "channel_id": channel,
            "provider": provider,
        }
        # Optional fields
        if external_reference: payload["external_reference"] = external_reference
        if customer_name: payload["customer_name"] = customer_name
        if callback_url: payload["callback_url"] = callback_url
        if credential_id: payload["credential_id"] = credential_id
        if network_code: payload["network_code"] = network_code
        resp = self.client.request("POST", PAYMENTS_PATH, json=payload, basic=True)
        ref = reference or resp.get("reference") or external_reference or f"pay-{channel}-{amount}"
        txn = PayHeroTransaction.objects.create(
            reference=ref,
            provider=provider,
            channel_id=channel,
            amount=amount,
            phone_number=phone_number,
            description=external_reference,
            operation_type="payment",
            status=resp.get("status", PayHeroTransaction.Status.QUEUED),
            metadata={"initiate_response": resp},
        )
        return {"reference": txn.reference, "status": txn.status, "raw": resp}

    @transaction.atomic
    def withdraw_mobile(self, *, amount: int, phone_number: str, network_code: str, channel_id: Optional[int] = None,
                        provider: str, external_reference: str | None = None, callback_url: str | None = None) -> Dict[str, Any]:
        """Initiate a mobile B2C withdrawal to the recipient phone number."""
        # For withdraw, prefer an explicit withdraw_channel_id, then default
        settings = self.client.settings
        channel = channel_id if channel_id is not None else (settings.withdraw_channel_id or settings.default_channel_id)
        if channel is None:
            raise PayHeroConfigurationError("Missing channel_id and PAYHERO_CHANNEL_ID not configured")
        payload: Dict[str, Any] = {
            "amount": amount,
            "phone_number": phone_number,
            "network_code": network_code,
            "channel": "mobile",
            "channel_id": channel,
            "payment_service": "b2c",
        }
        if external_reference: payload["external_reference"] = external_reference
        if callback_url: payload["callback_url"] = callback_url
        resp = self.client.request("POST", WITHDRAW_PATH, json=payload, basic=True)
        ref = external_reference or resp.get("merchant_reference") or f"wd-{channel}-{amount}"
        txn = PayHeroTransaction.objects.create(
            reference=ref,
            provider=provider,
            channel_id=channel,
            amount=amount,
            phone_number=phone_number,
            description=external_reference,
            operation_type="withdraw",
            status=resp.get("status", PayHeroTransaction.Status.QUEUED),
            metadata={"withdraw_response": resp},
        )
        return {"reference": txn.reference, "status": txn.status, "raw": resp}

    def list_transactions(self, *, page: int = 1, per: int = 20) -> Dict[str, Any]:
        """List transactions from the upstream PayHero v2 API (paginated)."""
        resp = self.client.request("GET", TRANSACTIONS_PATH, params={"page": page, "per": per}, basic=True)
        return resp

    def fetch_status(self, reference: str) -> Dict[str, Any]:
        """Fetch latest status for a previously recorded local transaction and sync it."""
        txn = PayHeroTransaction.objects.get(reference=reference)
        resp = self.client.request("GET", TRANSACTION_STATUS_PATH, params={"reference": reference}, basic=True)
        remote_status = resp.get("status") or resp.get("Status")
        if remote_status and remote_status != txn.status:
            txn.status = remote_status
            txn.last_status_payload = resp
            txn.metadata.update({"last_status_response": resp})
            txn.save(update_fields=["status", "last_status_payload", "metadata", "updated_at"])
        return {"reference": txn.reference, "current_status": txn.status, "raw": resp}

    # ------------------ Global (Bearer) ------------------
    def global_discovery(self, country: str = "KE") -> Dict[str, Any]:
        return self.client.request("GET", GLOBAL_DISCOVERY_PATH, params={"country": country}, bearer=True)

    @transaction.atomic
    def global_payment(self, *, request_type: str, provider: str, amount: float, currency: str,
                        country: str, reference: str, customer: Dict[str, Any], provider_config: Dict[str, Any],
                        vendor_config: Dict[str, Any], description: str | None = None, callback_url: str | None = None,
                        ipn_id: str | None = None) -> Dict[str, Any]:
        """Initiate a global/bearer payment with full configuration blocks."""
        payload: Dict[str, Any] = {
            "request_type": request_type,
            "provider": provider,
            "amount": amount,
            "currency": currency,
            "country": country,
            "reference": reference,
            "customer": customer,
            "provider_config": provider_config,
            "vendor_config": vendor_config,
        }
        if description: payload["description"] = description
        if callback_url: payload["callback_url"] = callback_url
        if ipn_id: payload["ipn_id"] = ipn_id
        resp = self.client.request("POST", GLOBAL_PAYMENTS_PATH, json=payload, bearer=True)
        txn = PayHeroTransaction.objects.create(
            reference=reference,
            provider=provider,
            amount=amount,
            currency=currency,
            description=description,
            operation_type="global",
            status=resp.get("status") or resp.get("Status") or PayHeroTransaction.Status.QUEUED,
            metadata={"global_payment_response": resp},
        )
        return {"reference": txn.reference, "status": txn.status, "raw": resp}
