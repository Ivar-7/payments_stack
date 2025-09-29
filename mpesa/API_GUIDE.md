# M-Pesa API - Complete Documentation

## Overview
Clean, modular M-Pesa integration with **zero redundancy**. Complete separation of concerns.

## Architecture
- **Views**: Handle HTTP only (ultra-thin wrappers)
- **Services**: Handle ALL business logic  
- **Models**: Handle data persistence only

## Services Structure

### PaymentService (`services/payment.py`)
**Purpose**: Unified coordinator with standardized responses
- `initiate_stk_payment(user, payment_data)` 
- `initiate_b2c_transfer(user, transfer_data)`
- `get_payment_status(checkout_request_id, conversation_id)`
- `get_user_transactions(user, transaction_type, limit)`
- `get_transaction_summary(user, days)`

### STKPushService (`services/stk_push.py`) 
**Purpose**: Customer-to-Business payments
- `initiate_payment(phone, amount, **options)`
- `get_access_token()`, `validate_phone_number()`, `validate_amount()`

### B2CTransferService (`services/b2c_transfer.py`)
**Purpose**: Business-to-Customer transfers  
- `send_money(phone, amount, **options)`
- `get_transfer_status(conversation_id)`

### CallbackService (`services/callback.py`)
**Purpose**: ALL callback handling (including HTTP parsing)
- `process_stk_callback_request(request)` 
- `process_b2c_result_request(request)`
- `process_b2c_timeout_request(request)`
- `handle_stk_callback(data)`, `handle_b2c_result(data)`, `handle_b2c_timeout(data)`

### TransactionService (`services/transaction.py`)
**Purpose**: Transaction queries and reporting
- `get_user_transactions(user_id, transaction_type, limit)`
- `get_transaction_summary(user_id, days)`  
- `search_transactions(query, user_id, limit)`
- `get_failed_transactions(user_id, limit)`

## API Endpoints

### 1. STK Push Payment
```
POST /mpesa/stk-push/
Authorization: Bearer <token>

{
    "phone": "254712345678",
    "amount": 100,
    "payment_type": "product",
    "product_id": 123,
    "account_reference": "SKY-PROD-123",
    "transaction_desc": "Payment for Product #123"
}
```

### 2. Send Money (B2C Transfer)
```
POST /mpesa/send-money/
Authorization: Bearer <token>

{
    "phone": "254712345678", 
    "amount": 50,
    "occasion": "Referral bonus",
    "remarks": "Bonus payment from Skyfield",
    "command_id": "BusinessPayment",
    "reference": "REF-001"
}
```

### 3. Payment Status
```
GET /mpesa/payment-status/?checkout_request_id=ws_CO_....
GET /mpesa/payment-status/?conversation_id=AG_....
Authorization: Bearer <token>
```

### 4. User Transactions  
```
GET /mpesa/transactions/?type=stk_push&limit=50
GET /mpesa/transactions/?type=b2c_transfer&limit=20
GET /mpesa/transactions/  # All types
Authorization: Bearer <token>
```

### 5. Transaction Summary
```
GET /mpesa/transaction-summary/?days=30
Authorization: Bearer <token>
```

## Callback Endpoints (No Auth)
- `POST /mpesa/callback/` - STK Push callbacks
- `POST /mpesa/b2c-result/` - B2C result callbacks  
- `POST /mpesa/b2c-timeout/` - B2C timeout callbacks

## Clean Architecture Benefits ✅
- **Ultra-thin views** (2-6 lines each)
- **Zero code duplication** 
- **Complete modularity**
- **Single source of truth**
- **Services handle ALL logic**
- **Standardized responses**
- **High testability**

## Fixed Issues ✅
- **TransactionService**: Now properly filters STK transactions by user_id
- **MpesaTransaction model**: Added missing user_id field
- **Complete user tracking**: Both STK and B2C transactions track users
- **Documentation**: Single consolidated guide (no more redundant files)