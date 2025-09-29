"""
M-Pesa Payment Service
Coordinates payment operations and provides unified interface
"""
from rest_framework.response import Response
from rest_framework import status
from .stk_push import STKPushService
from .b2c_transfer import B2CTransferService
from .callback import CallbackService
from .transaction import TransactionService


class PaymentService:
    """
    Unified payment service that coordinates different payment types
    Provides standard response formatting and error handling
    """
    
    def __init__(self):
        self.stk_service = STKPushService()
        self.b2c_service = B2CTransferService()
        self.callback_service = CallbackService()
        self.transaction_service = TransactionService()
    
    def initiate_stk_payment(self, user, payment_data):
        """
        Initiate STK Push payment with standardized response
        
        Args:
            user: Authenticated user
            payment_data: Dictionary with payment information
        """
        try:
            # Extract and validate data
            phone = payment_data.get('phone')
            amount = payment_data.get('amount')
            payment_type = payment_data.get('payment_type', 'product')
            product_id = payment_data.get('product_id')
            subscription_plan_id = payment_data.get('subscription_plan_id')
            account_reference = payment_data.get('account_reference', f'SKYFIELD-{user.id}')
            transaction_desc = payment_data.get('transaction_desc', 'Payment for Skyfield services')
            
            # Validate required fields
            if not phone or not amount:
                return Response({
                    'error': 'Phone number and amount are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Make payment request
            result = self.stk_service.initiate_payment(
                phone=phone,
                amount=amount,
                payment_type=payment_type,
                product_id=product_id,
                subscription_plan_id=subscription_plan_id,
                account_reference=account_reference,
                transaction_desc=transaction_desc,
                user_id=user.id
            )
            
            # Format response
            if result.get('ResponseCode') == '0':
                return Response({
                    'success': True,
                    'message': 'Payment request sent successfully',
                    'data': {
                        'checkout_request_id': result.get('CheckoutRequestID'),
                        'merchant_request_id': result.get('MerchantRequestID'),
                        'customer_message': result.get('CustomerMessage')
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': result.get('ResponseDescription', 'Payment initiation failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'Payment initiation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def initiate_b2c_transfer(self, user, transfer_data):
        """
        Initiate B2C money transfer with standardized response
        
        Args:
            user: Authenticated user
            transfer_data: Dictionary with transfer information
        """
        try:
            # Extract and validate data
            phone = transfer_data.get('phone')
            amount = transfer_data.get('amount')
            occasion = transfer_data.get('occasion', 'Money transfer')
            remarks = transfer_data.get('remarks', 'Payment from Skyfield')
            command_id = transfer_data.get('command_id', 'BusinessPayment')
            reference = transfer_data.get('reference')
            
            # Validate required fields
            if not phone or not amount:
                return Response({
                    'error': 'Phone number and amount are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Make transfer request
            result = self.b2c_service.send_money(
                phone=phone,
                amount=amount,
                occasion=occasion,
                remarks=remarks,
                command_id=command_id,
                user_id=user.id,
                reference=reference
            )
            
            # Format response
            if result.get('ResponseCode') == '0':
                return Response({
                    'success': True,
                    'message': 'Money transfer initiated successfully',
                    'data': {
                        'conversation_id': result.get('ConversationID'),
                        'originator_conversation_id': result.get('OriginatorConversationID'),
                        'transaction_id': result.get('transaction_id')
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': result.get('ResponseDescription', 'Money transfer failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'Money transfer failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_payment_status(self, checkout_request_id=None, conversation_id=None):
        """
        Get payment status with standardized response
        """
        try:
            if not checkout_request_id and not conversation_id:
                return Response({
                    'error': 'Either checkout_request_id or conversation_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = self.callback_service.get_transaction_status(
                checkout_request_id=checkout_request_id,
                conversation_id=conversation_id
            )
            
            if result.get('status') == 'error':
                return Response({
                    'error': result.get('message')
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to get payment status: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_user_transactions(self, user, transaction_type=None, limit=50):
        """
        Get user transactions with standardized response
        """
        try:
            transactions = self.transaction_service.get_user_transactions(
                user_id=user.id,
                transaction_type=transaction_type,
                limit=limit
            )
            
            return Response({
                'success': True,
                'data': {
                    'transactions': transactions,
                    'count': len(transactions)
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to get transactions: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_transaction_summary(self, user, days=30):
        """
        Get transaction summary with standardized response
        """
        try:
            summary = self.transaction_service.get_transaction_summary(
                user_id=user.id,
                days=days
            )
            
            return Response({
                'success': True,
                'data': summary
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to get transaction summary: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)