"""
M-Pesa Views - Clean Modular Implementation
Uses individual service classes for better separation of concerns
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .services import CallbackService


def index(request):
    """Simple index page"""
    return render(request, 'index.html')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stk_push_payment(request):
    """
    Initiate STK Push payment (Customer pays Business)
    Used for: Product purchases, subscription payments, etc.
    """
    from .services.stk_push import STKPushService
    from .services.transaction import TransactionService
    
    try:
        stk_service = STKPushService()
        
        # Extract and validate data
        phone = request.data.get('phone')
        amount = request.data.get('amount')
        payment_type = request.data.get('payment_type', 'product')
        product_id = request.data.get('product_id')
        subscription_plan_id = request.data.get('subscription_plan_id')
        account_reference = request.data.get('account_reference', f'SKYFIELD-{request.user.id}')
        transaction_desc = request.data.get('transaction_desc', 'Payment for Skyfield services')
        
        # Validate required fields
        if not phone or not amount:
            return Response({
                'error': 'Phone number and amount are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Make payment request
        result = stk_service.initiate_payment(
            phone=phone,
            amount=amount,
            payment_type=payment_type,
            product_id=product_id,
            subscription_plan_id=subscription_plan_id,
            account_reference=account_reference,
            transaction_desc=transaction_desc,
            user_id=request.user.id
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_money(request):
    """
    Send money to customer (B2C Transfer - Business pays Customer)
    Used for: Referral payouts, refunds, rewards, etc.
    """
    from .services.b2c_transfer import B2CTransferService
    
    try:
        b2c_service = B2CTransferService()
        
        # Extract and validate data
        phone = request.data.get('phone')
        amount = request.data.get('amount')
        occasion = request.data.get('occasion', 'Money transfer')
        remarks = request.data.get('remarks', 'Payment from Skyfield')
        command_id = request.data.get('command_id', 'BusinessPayment')
        reference = request.data.get('reference')
        
        # Validate required fields
        if not phone or not amount:
            return Response({
                'error': 'Phone number and amount are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Make transfer request
        result = b2c_service.send_money(
            phone=phone,
            amount=amount,
            occasion=occasion,
            remarks=remarks,
            command_id=command_id,
            user_id=request.user.id,
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request):
    """Get payment status by checkout_request_id or conversation_id"""
    from .services.callback import CallbackService
    
    try:
        callback_service = CallbackService()
        checkout_request_id = request.GET.get('checkout_request_id')
        conversation_id = request.GET.get('conversation_id')
        
        if not checkout_request_id and not conversation_id:
            return Response({
                'error': 'Either checkout_request_id or conversation_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = callback_service.get_transaction_status(
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_transactions(request):
    """Get user's transaction history"""
    from .services.transaction import TransactionService
    
    try:
        transaction_service = TransactionService()
        transaction_type = request.GET.get('type')  # stk_push, b2c_transfer, or None for all
        limit = int(request.GET.get('limit', 50))
        
        transactions = transaction_service.get_user_transactions(
            user_id=request.user.id,
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_summary(request):
    """Get transaction summary for user"""
    from .services.transaction import TransactionService
    
    try:
        transaction_service = TransactionService()
        days = int(request.GET.get('days', 30))
        
        summary = transaction_service.get_transaction_summary(
            user_id=request.user.id,
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


# Callback endpoints (no authentication required)
@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """Handle STK Push callback from Safaricom"""
    callback_service = CallbackService()
    return callback_service.process_stk_callback_request(request)


@csrf_exempt
@require_http_methods(["POST"])
def b2c_result_callback(request):
    """Handle B2C result callback from Safaricom"""
    callback_service = CallbackService()
    return callback_service.process_b2c_result_request(request)


@csrf_exempt
@require_http_methods(["POST"])
def b2c_timeout_callback(request):
    """Handle B2C timeout callback from Safaricom"""
    callback_service = CallbackService()
    return callback_service.process_b2c_timeout_request(request)