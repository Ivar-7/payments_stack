"""
M-Pesa B2C Transfer Service
Handles sending money to customers (B2C)
"""
import requests
import json
from requests.auth import HTTPBasicAuth
from decouple import config
from ..models import MpesaB2CTransaction
from django.conf import settings


class B2CTransferService:
    def __init__(self):
        self.consumer_key = config('CONSUMER_KEY')
        self.consumer_secret = config('CONSUMER_SECRET')
        self.business_shortcode = config('B2C_SHORTCODE', default=config('BUSINESS_SHORTCODE'))
        self.initiator_name = config('INITIATOR_NAME', default='testapi')
        # Require credentials and callback URLs from environment (no hard-coded defaults)
        self.security_credential = config('SECURITY_CREDENTIAL', default=None)
        if not self.security_credential:
            raise ValueError('SECURITY_CREDENTIAL must be set in environment variables')

        self.queue_timeout_url = config('B2C_QUEUE_TIMEOUT_URL', default=None)
        self.result_url = config('B2C_RESULT_URL', default=None)
        if not self.queue_timeout_url or not self.result_url:
            raise ValueError('B2C_QUEUE_TIMEOUT_URL and B2C_RESULT_URL must be set in environment variables')

    def _base_host(self) -> str:
        return 'https://sandbox.safaricom.co.ke' if getattr(settings, 'DEBUG', False) else 'https://api.safaricom.co.ke'
        
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
            
    def send_money(self, phone, amount, occasion="Payment", remarks="Money transfer", 
                   command_id="BusinessPayment", user_id=None, reference=None):
        """
        Send money to customer
        
        Args:
            phone: Customer phone number (254XXXXXXXXX)
            amount: Amount to send
            occasion: Occasion for the payment
            remarks: Remarks for the payment
            command_id: BusinessPayment, SalaryPayment, or PromotionPayment
            user_id: User ID if this is linked to a user
            reference: Reference for tracking
        """
        
        # Validate inputs
        phone = self.validate_phone_number(phone)
        amount = self.validate_amount(amount)
        
        # Validate command_id
        valid_commands = ["BusinessPayment", "SalaryPayment", "PromotionPayment"]
        if command_id not in valid_commands:
            raise ValueError(f"Invalid command_id. Must be one of: {valid_commands}")
        
        # Get access token
        access_token = self.get_access_token()
        
        # Prepare payload
        payload = {
            "InitiatorName": self.initiator_name,
            "SecurityCredential": self.security_credential,
            "CommandID": command_id,
            "Amount": amount,
            "PartyA": self.business_shortcode,
            "PartyB": phone,
            "Remarks": remarks,
            "QueueTimeOutURL": self.queue_timeout_url,
            "ResultURL": self.result_url,
            "Occasion": occasion
        }
        
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
        
        try:
            # Make API request
            response = requests.post(
                f"{self._base_host()}/mpesa/b2c/v1/paymentrequest",
                json=payload,
                headers=headers,
                timeout=20
            )
            response.raise_for_status()
            response_data = response.json()
            
            # Store transaction in database
            if response_data.get('ResponseCode') == '0':
                transaction = MpesaB2CTransaction.objects.create(
                    conversation_id=response_data.get('ConversationID', ''),
                    originator_conversation_id=response_data.get('OriginatorConversationID', ''),
                    response_code=response_data.get('ResponseCode', ''),
                    response_description=response_data.get('ResponseDescription', ''),
                    amount=amount,
                    phone_number=phone,
                    command_id=command_id,
                    remarks=remarks,
                    occasion=occasion,
                    user_id=user_id,
                    reference=reference
                )
                
                # Add transaction ID to response
                response_data['transaction_id'] = transaction.id
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"B2C transfer request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to send money: {str(e)}")
            
    def get_transfer_status(self, conversation_id):
        """Get transfer status by conversation ID"""
        try:
            transaction = MpesaB2CTransaction.objects.get(conversation_id=conversation_id)
            
            status = "pending"
            if transaction.result_code == 0:
                status = "success"
            elif transaction.result_code is not None and transaction.result_code != 0:
                status = "failed"
                
            return {
                'status': status,
                'transaction': {
                    'id': transaction.id,
                    'conversation_id': transaction.conversation_id,
                    'originator_conversation_id': transaction.originator_conversation_id,
                    'result_code': transaction.result_code,
                    'result_description': transaction.result_description,
                    'amount': float(transaction.amount) if transaction.amount else None,
                    'phone_number': transaction.phone_number,
                    'mpesa_receipt_number': transaction.mpesa_receipt_number,
                    'transaction_date': str(transaction.transaction_date) if transaction.transaction_date else None,
                    'created_at': transaction.created_at.isoformat(),
                    'updated_at': transaction.updated_at.isoformat()
                }
            }
            
        except MpesaB2CTransaction.DoesNotExist:
            raise Exception("Transfer not found")