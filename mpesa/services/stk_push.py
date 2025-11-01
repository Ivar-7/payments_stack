"""
M-Pesa STK Push Service
Handles customer payment requests (C2B)
"""
import requests
import datetime
import base64
import json
from requests.auth import HTTPBasicAuth
from decouple import config
from ..models import MpesaTransaction
from django.conf import settings


class STKPushService:
    def __init__(self):
        self.consumer_key = config('CONSUMER_KEY')
        self.consumer_secret = config('CONSUMER_SECRET')
        self.passkey = config('PASSKEY')
        self.business_shortcode = config('BUSINESS_SHORTCODE')
        # Require callback URL from environment (no hard-coded defaults)
        self.callback_url = config('CALLBACK_URL', default=None)
        if not self.callback_url:
            raise ValueError('CALLBACK_URL must be set in environment variables')

    def _base_host(self) -> str:
        """Return Safaricom API host based on DEBUG flag."""
        return 'https://api.safaricom.co.ke' if getattr(settings, 'DEBUG', False) else 'https://api.safaricom.co.ke'
        
    def get_access_token(self):
        """Get access token from Safaricom API"""
        api_url = f"{self._base_host()}/oauth/v1/generate?grant_type=client_credentials"
        
        try:
            response = requests.get(
                api_url,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                timeout=15
            )
            response.raise_for_status()
            token_data = response.json()
            return f"Bearer {token_data['access_token']}"
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get access token: {str(e)}")
            
    def generate_password(self):
        """Generate password for STK Push"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = self.business_shortcode + self.passkey + timestamp
        encoded = base64.b64encode(data_to_encode.encode())
        return encoded.decode('utf-8'), timestamp
        
    def validate_phone_number(self, phone):
        """Validate and format phone number"""
        if not phone or not phone.startswith('254') or len(phone) != 12:
            raise ValueError("Invalid phone number. Use format 254XXXXXXXXX")
        return phone
        
    def validate_amount(self, amount):
        """Validate amount"""
        try:
            amount_int = int(amount)
            if amount_int < 1:
                raise ValueError("Amount must be at least 1")
            return amount_int
        except (ValueError, TypeError):
            raise ValueError("Invalid amount. Must be a positive number")
            
    def initiate_payment(self, phone, amount, account_reference="Skyfield", transaction_desc="Payment", 
                         payment_type="product", product_id=None, subscription_plan_id=None, user_id=None):
        """Initiate STK Push payment request"""
        
        # Validate inputs
        phone = self.validate_phone_number(phone)
        amount = self.validate_amount(amount)
        
        # Get access token and password
        access_token = self.get_access_token()
        password, timestamp = self.generate_password()
        
        # Prepare payload
        payload = {
            "BusinessShortCode": self.business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": self.business_shortcode,
            "PhoneNumber": phone,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
        
        try:
            # Make API request
            response = requests.post(
                f"{self._base_host()}/mpesa/stkpush/v1/processrequest",
                json=payload,
                headers=headers,
                timeout=20
            )
            response.raise_for_status()
            response_data = response.json()
            
            # Store transaction in database if successful
            if response_data.get('ResponseCode') == '0':
                MpesaTransaction.objects.create(
                    merchant_request_id=response_data.get('MerchantRequestID', ''),
                    checkout_request_id=response_data.get('CheckoutRequestID', ''),
                    result_code=None,  # Pending until callback updates
                    result_desc='Payment request initiated',
                    amount=amount,
                    phone_number=phone,
                    payment_type=payment_type,
                    product_id=product_id,
                    subscription_plan_id=subscription_plan_id,
                    account_reference=account_reference,
                    transaction_desc=transaction_desc,
                    user_id=user_id
                )
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"STK Push request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to initiate STK Push: {str(e)}")