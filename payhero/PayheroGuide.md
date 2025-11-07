## PayHero Kenya API – Condensed Integration Guide

Base URL: https://backend.payhero.co.ke

This guide summarizes only what’s needed to implement server‑side integration.

### Authentication
- Basic (v2 endpoints): Authorization: Basic <base64(username:password)>
  - basicAuthToken = base64("API_USERNAME:API_PASSWORD")
- Bearer (Global endpoints): Authorization: Bearer <token>

Common headers:
- Content-Type: application/json (for POST)
- Authorization: as above

---

## v2 Endpoints (Basic auth)

### 1) Service Wallet Balance
- GET /api/v2/wallets?wallet_type=service_wallet
- Auth: Basic
- Response keys: id, account_id, wallet_type, currency, available_balance, created_at, updated_at

### 2) Payments Wallet Balance
- GET /api/v2/payment_channels/{wallet_channel_id}
- Auth: Basic
- Response keys (subset): id, channel_type, description, is_active, balance_plain.balance, created_at, updated_at

### 3) Service Wallet Top Up (MPESA STK to fund service wallet)
- POST /api/v2/topup
- Auth: Basic
- Body:
  - amount (integer, required)
  - phone_number (string, required)
- Response keys: success (bool), status (QUEUED), reference, CheckoutRequestID

### 4) Initiate MPESA STK Push (receive customer payment)
- POST /api/v2/payments
- Auth: Basic
- Body:
  - amount (int, required)
  - phone_number (string, required)
  - channel_id (int, required)
  - provider (string, required: "m-pesa" or "sasapay")
  - external_reference (string, optional)
  - customer_name (string, optional)
  - callback_url (string, optional)
  - credential_id (string, optional)
  - network_code (string, required when using wallet channel with provider=sasapay; e.g., 63902 for MPESA)
- Response keys: success, status (QUEUED), reference, CheckoutRequestID

Callback (payment) example payload (POST to your callback_url):
{
  "forward_url": "",
  "response": {
    "Amount": 10,
    "CheckoutRequestID": "...",
    "ExternalReference": "INV-009",
    "MerchantRequestID": "...",
    "MpesaReceiptNumber": "...",
    "Phone": "+2547...",
    "ResultCode": 0,
    "ResultDesc": "The service request is processed successfully.",
    "Status": "Success"
  },
  "status": true
}

### 5) Withdraw From Payments Wallet → Mobile (B2C)
- POST /api/v2/withdraw
- Auth: Basic
- Body:
  - external_reference (string, optional but recommended)
  - amount (int, required)
  - phone_number (string, required, in MSISDN format starting with country code)
  - network_code (string, required: 63902=MPESA, 63903=Airtel)
  - callback_url (string, optional)
  - channel (string, required: "mobile")
  - channel_id (int, required; your Payments Wallet Channel ID)
  - payment_service (string, required: "b2c")
- Response keys: status (QUEUED), merchant_reference, checkout_request_id, response_code, conversation_id

Callback (withdrawal) example payload:
{
  "forward_url": "",
  "response": {
    "Amount": 50,
    "CheckoutRequestID": "...",
    "ExternalReference": "TX1234...",
    "MerchantRequestID": "...",
    "RecipientAccountNumber": "2547...",
    "ResultCode": 0,
    "ResultDesc": "Transaction processed successfully.",
    "Status": "Success",
    "TransactionID": "..."
  },
  "status": true
}

### 6) Account Transactions (paginated)
- GET /api/v2/transactions?page={int}&per={int}
- Auth: Basic
- Response: transactions [ ... ], pagination { page, per, count, next_page, prev_page, num_pages }

### 7) Transaction Status
- GET /api/v2/transaction-status?reference={string}
- Auth: Basic
- Response keys (subset): transaction_date, provider, success, status, reference, provider_reference
- Status values: QUEUED | SUCCESS | FAILED

---

## Global Endpoints (Bearer auth)

### 8) Discovery – Payment World
- GET /api/global/discovery/payment-world/?country=KE
- Auth: Bearer <token>
- Response (high‑level):
  - rails: { bank, card, momo }
  - available_providers: by rail
  - provider_networks: details per provider (incl. code/provider_id, limits)
  - required_fields: per provider/network (e.g., provider_config.provider_id, customer fields, redirect_url for cards)
  - provider_operations: c2b/b2c support per provider
  - payment_limits, fees, supported_currencies
  - api_endpoints metadata

Notes:
- Keep provider_networks[provider][network].code (e.g., "2031") as provider_id for global payments.

### 9) Global Payments
- POST /api/global/payments
- Auth: Bearer <token>
- Body:
  - request_type (string, required): one of topup | payment | withdrawal | utility | bills
  - provider (string, required): bitlipa | intasend | sasapay | pesapal | m-pesa | bank
  - amount (number, required)
  - currency (string, required)
  - country (string, required)
  - reference (string, required)
  - description (string, optional)
  - customer (object, required fields vary; phone/email/first_name/last_name; address required for card)
  - provider_config (object): includes provider_id (required from discovery), plus optional merchant_id, category, etc.
  - vendor_config (object): vendor_id (required), channel_id (required)
  - callback_url (string, optional)
  - ipn_id (string, optional)
- Response keys (subset): status_code, merchant_reference, transaction_type, success, message, checkout_request_id, gateway, conversation_id, provider_response{ ... }

---

## Reference
- Network codes: 63902 (MPESA), 63903 (Airtel)
- wallet_type for service wallet balance: service_wallet
- Auth summary:
  - v2 endpoints → Basic Authorization
  - Global discovery/payments → Bearer Authorization

This document omits verbose language‑specific samples and focuses on fields/paths required to implement the integration.