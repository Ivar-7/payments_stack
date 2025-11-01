"""
M-Pesa Callback Service
Handles all M-Pesa callback processing
"""
import json
from django.utils import timezone
from django.http import JsonResponse
from ..models import MpesaTransaction, MpesaB2CTransaction


class CallbackService:
    
    def process_stk_callback_request(self, request):
        """
        Process STK Push callback HTTP request
        Parses request body and delegates to handle_stk_callback
        """
        try:
            data = json.loads(request.body.decode('utf-8'))
            result = self.handle_stk_callback(data)
            
            return JsonResponse({
                'ResultCode': 0,
                'ResultDesc': 'Callback processed successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'ResultCode': 1,
                'ResultDesc': f'Callback processing failed: {str(e)}'
            })
    
    def process_b2c_result_request(self, request):
        """
        Process B2C result callback HTTP request
        Parses request body and delegates to handle_b2c_result
        """
        try:
            data = json.loads(request.body.decode('utf-8'))
            result = self.handle_b2c_result(data)
            
            return JsonResponse({
                'ResultCode': 0,
                'ResultDesc': 'B2C callback processed successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'ResultCode': 1,
                'ResultDesc': f'B2C callback processing failed: {str(e)}'
            })
    
    def process_b2c_timeout_request(self, request):
        """
        Process B2C timeout callback HTTP request
        Parses request body and delegates to handle_b2c_timeout
        """
        try:
            data = json.loads(request.body.decode('utf-8'))
            result = self.handle_b2c_timeout(data)
            
            return JsonResponse({
                'ResultCode': 0,
                'ResultDesc': 'B2C timeout processed successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'ResultCode': 1,
                'ResultDesc': f'B2C timeout processing failed: {str(e)}'
            })
    
    def handle_stk_callback(self, request_data):
        """
        Handle STK Push callback
        Updates transaction status based on callback data
        """
        try:
            stkCallback = request_data.get('Body', {}).get('stkCallback', {})
            
            merchant_request_id = stkCallback.get('MerchantRequestID')
            checkout_request_id = stkCallback.get('CheckoutRequestID')
            result_code = stkCallback.get('ResultCode', -1)
            result_desc = stkCallback.get('ResultDesc', 'Unknown error')
            
            if not merchant_request_id or not checkout_request_id:
                return {
                    'status': 'error',
                    'message': 'Missing required callback data'
                }
            
            # Find the transaction
            try:
                transaction = MpesaTransaction.objects.get(
                    merchant_request_id=merchant_request_id,
                    checkout_request_id=checkout_request_id
                )
            except MpesaTransaction.DoesNotExist:
                return {
                    'status': 'error',
                    'message': 'Transaction not found'
                }
            
            # Update transaction with callback data
            transaction.result_code = result_code
            transaction.result_desc = result_desc
            
            # If successful, extract additional details
            if result_code == 0:
                callback_metadata = stkCallback.get('CallbackMetadata', {})
                items = callback_metadata.get('Item', [])
                
                for item in items:
                    name = item.get('Name')
                    value = item.get('Value')
                    
                    if name == 'Amount':
                        transaction.amount = value
                    elif name == 'MpesaReceiptNumber':
                        transaction.mpesa_receipt_number = value
                    elif name == 'TransactionDate':
                        transaction.transaction_date = value
                    elif name == 'PhoneNumber':
                        transaction.phone_number = value
            
            transaction.save()
            
            # If payment successful, handle subscription activation
            if result_code == 0:
                self._handle_successful_subscription_payment(transaction)
            
            return {
                'status': 'success',
                'message': 'Callback processed successfully',
                'transaction_id': transaction.id,
                'result_code': result_code
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Callback processing failed: {str(e)}'
            }
    
    def handle_b2c_result(self, request_data):
        """
        Handle B2C Result callback
        Updates B2C transaction status based on callback data
        """
        try:
            result = request_data.get('Result', {})
            
            conversation_id = result.get('ConversationID')
            originator_conversation_id = result.get('OriginatorConversationID')
            result_code = result.get('ResultCode', -1)
            result_desc = result.get('ResultDesc', 'Unknown error')
            
            if not conversation_id:
                return {
                    'status': 'error',
                    'message': 'Missing ConversationID in callback'
                }
            
            # Find the transaction
            try:
                transaction = MpesaB2CTransaction.objects.get(
                    conversation_id=conversation_id
                )
            except MpesaB2CTransaction.DoesNotExist:
                return {
                    'status': 'error',
                    'message': 'B2C Transaction not found'
                }
            
            # Update transaction with result data
            transaction.result_code = result_code
            transaction.result_description = result_desc
            
            # If successful, extract additional details
            if result_code == 0:
                result_parameters = result.get('ResultParameters', {})
                parameters = result_parameters.get('ResultParameter', [])
                
                for param in parameters:
                    key = param.get('Key')
                    value = param.get('Value')
                    
                    if key == 'TransactionReceipt':
                        transaction.mpesa_receipt_number = value
                    elif key == 'TransactionCompletedDateTime':
                        transaction.transaction_completed_date = value
                    elif key == 'B2CUtilityAccountAvailableFunds':
                        transaction.b2c_utility_account_available_funds = value
                    elif key == 'B2CWorkingAccountAvailableFunds':
                        transaction.b2c_working_account_available_funds = value
                    elif key == 'B2CChargesPaidAccountAvailableFunds':
                        transaction.b2c_charges_paid_account_available_funds = value
                    elif key == 'ReceiverPartyPublicName':
                        transaction.receiver_party_public_name = value
                    elif key == 'TransactionAmount':
                        # This is often returned as confirmation
                        pass
            
            transaction.save()
            
            return {
                'status': 'success',
                'message': 'B2C callback processed successfully',
                'transaction_id': transaction.id,
                'result_code': result_code
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'B2C callback processing failed: {str(e)}'
            }
    
    def handle_b2c_timeout(self, request_data):
        """
        Handle B2C Timeout callback
        Marks transaction as timed out
        """
        try:
            result = request_data.get('Result', {})
            conversation_id = result.get('ConversationID')
            
            if not conversation_id:
                return {
                    'status': 'error',
                    'message': 'Missing ConversationID in timeout callback'
                }
            
            # Find the transaction
            try:
                transaction = MpesaB2CTransaction.objects.get(
                    conversation_id=conversation_id
                )
            except MpesaB2CTransaction.DoesNotExist:
                return {
                    'status': 'error',
                    'message': 'B2C Transaction not found'
                }
            
            # Mark as timed out
            transaction.result_code = -1
            transaction.result_description = 'Request timeout'
            transaction.save()
            
            return {
                'status': 'success',
                'message': 'B2C timeout processed successfully',
                'transaction_id': transaction.id
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'B2C timeout processing failed: {str(e)}'
            }
    
    def get_transaction_status(self, checkout_request_id=None, conversation_id=None):
        """
        Get transaction status by either checkout_request_id (STK) or conversation_id (B2C)
        """
        try:
            if checkout_request_id:
                # STK Push transaction
                transaction = MpesaTransaction.objects.get(
                    checkout_request_id=checkout_request_id
                )
                
                status = "pending"
                if transaction.result_code == 0:
                    status = "success"
                elif transaction.result_code is not None and transaction.result_code != 0:
                    status = "failed"
                
                return {
                    'type': 'stk_push',
                    'status': status,
                    'transaction': {
                        'id': transaction.id,
                        'merchant_request_id': transaction.merchant_request_id,
                        'checkout_request_id': transaction.checkout_request_id,
                        'result_code': transaction.result_code,
                        'result_desc': transaction.result_desc,
                        'amount': float(transaction.amount) if transaction.amount else None,
                        'mpesa_receipt_number': transaction.mpesa_receipt_number,
                        'transaction_date': transaction.transaction_date,
                        'phone_number': transaction.phone_number,
                        'created_at': transaction.created_at.isoformat(),
                        'updated_at': transaction.updated_at.isoformat()
                    }
                }
                
            elif conversation_id:
                # B2C transaction
                transaction = MpesaB2CTransaction.objects.get(
                    conversation_id=conversation_id
                )
                
                status = "pending"
                if transaction.result_code == 0:
                    status = "success"
                elif transaction.result_code is not None and transaction.result_code != 0:
                    status = "failed"
                
                return {
                    'type': 'b2c_transfer',
                    'status': status,
                    'transaction': {
                        'id': transaction.id,
                        'conversation_id': transaction.conversation_id,
                        'originator_conversation_id': transaction.originator_conversation_id,
                        'result_code': transaction.result_code,
                        'result_description': transaction.result_description,
                        'amount': float(transaction.amount),
                        'phone_number': transaction.phone_number,
                        'mpesa_receipt_number': transaction.mpesa_receipt_number,
                        'transaction_date': transaction.transaction_date,
                        'created_at': transaction.created_at.isoformat(),
                        'updated_at': transaction.updated_at.isoformat()
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Either checkout_request_id or conversation_id is required'
                }
                
        except (MpesaTransaction.DoesNotExist, MpesaB2CTransaction.DoesNotExist):
            return {
                'status': 'error',
                'message': 'Transaction not found'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to get transaction status: {str(e)}'
            }
    
    def _handle_successful_subscription_payment(self, transaction):
        """Handle successful subscription payment and award referral points"""
        try:
            # Check if this is a subscription payment
            if not transaction.account_reference or 'Sub_' not in transaction.account_reference:
                return
            
            # Extract subscription ID from account_reference
            # Format: "Skyfield_{plan}_Sub_{subscription_id}"
            parts = transaction.account_reference.split('_')
            if len(parts) >= 3 and parts[-2] == 'Sub':
                subscription_id = parts[-1]
                
                # Import here to avoid circular imports
                from coreapis.models import Subscription, Referral
                from django.utils import timezone
                
                try:
                    subscription = Subscription.objects.get(id=subscription_id)
                    
                    # Activate subscription
                    subscription.status = 'active'
                    subscription.is_active = True
                    subscription.mpesa_receipt_number = transaction.mpesa_receipt_number
                    subscription.payment_date = timezone.now()
                    subscription.save()
                    
                    # Process referral points
                    user = subscription.user
                    try:
                        # Check if this user was referred and hasn't been awarded points yet
                        referral = Referral.objects.get(
                            referred=user,
                            is_subscription_complete=False
                        )
                        
                        # Award points to both referrer and referred user
                        referrer = referral.referrer
                        
                        # Award 1 point to referrer
                        referrer.points += 1
                        referrer.save()
                        
                        # Award 1 point to referred user
                        user.points += 1
                        user.save()
                        
                        # Update referral record
                        referral.is_subscription_complete = True
                        referral.points_awarded_to_referrer = 1
                        referral.points_awarded_to_referred = 1
                        referral.subscription_date = timezone.now()
                        referral.note = f"Points awarded - referrer and referred each earned 1 point"
                        referral.save()
                        
                    except Referral.DoesNotExist:
                        # User wasn't referred or already got points
                        pass
                        
                except Subscription.DoesNotExist:
                    pass
                    
        except Exception as e:
            # Log error but don't fail the callback
            pass