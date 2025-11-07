from django.urls import path
from .views import (
    ServiceWalletBalanceView,
    PaymentChannelBalanceView,
    TopupServiceWalletView,
    InitiatePaymentView,
    WithdrawMobileView,
    TransactionsListView,
    TransactionStatusView,
    GlobalDiscoveryView,
    GlobalPaymentView,
    WebhookReceiverView,
)

app_name = "payhero"

urlpatterns = [
    # v2 Basic auth endpoints
    path("wallets/service/", ServiceWalletBalanceView.as_view(), name="service-wallet"),
    path("wallets/channel/<int:channel_id>/", PaymentChannelBalanceView.as_view(), name="channel-wallet"),
    path("topup/", TopupServiceWalletView.as_view(), name="topup"),
    path("payments/initiate/", InitiatePaymentView.as_view(), name="initiate-payment"),
    path("withdraw/mobile/", WithdrawMobileView.as_view(), name="withdraw-mobile"),
    path("transactions/", TransactionsListView.as_view(), name="transactions"),
    path("transaction-status/", TransactionStatusView.as_view(), name="transaction-status"),
    # Global Bearer auth endpoints
    path("global/discovery/", GlobalDiscoveryView.as_view(), name="global-discovery"),
    path("global/payments/", GlobalPaymentView.as_view(), name="global-payments"),
    # Webhook
    path("webhooks/payhero/", WebhookReceiverView.as_view(), name="webhook"),
]