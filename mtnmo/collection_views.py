from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging
from django.views.decorators.csrf import csrf_exempt

from .models import CollectionTransaction, CollectionCallback
from .collection import Collection

logger = logging.getLogger(__name__)

# Utility functions to store collection transactions
def store_collection(status_response: dict) -> None:
    try:
        transaction = CollectionTransaction(
            financial_transaction_id=status_response.get('financialTransactionId', ''),
            external_id=status_response.get('externalId', ''),
            amount=status_response.get('amount', 0),
            currency=status_response.get('currency', ''),
            party_id_type=status_response.get('payer', {}).get('partyIdType', ''),
            party_id=status_response.get('payer', {}).get('partyId', ''),
            payer_message=status_response.get('payerMessage', ''),
            payee_note=status_response.get('payeeNote', ''),
            status=status_response.get('status', ''),
        )
        transaction.save()
    except Exception as e:
        logger.error(f"Error storing collection transaction: {e}")
        raise

# Collection API with secure CSRF handling
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def collection(request):
    try:
        coll = Collection()
        amount = request.data.get('amount')
        phone_number = request.data.get('phone')
        external_id = request.data.get('external_id')
        currency = request.data.get('currency')

        # Initiate the collection request
        response = coll.requestToPay(amount, phone_number, external_id, currency)
        # response["Access-Control-Allow-Credentials"] = "true"

        # Fetch the transaction status and store it
        status_response = coll.getTransactionStatus(response.get('ref', ''))
        store_collection(status_response)

        return Response({"status": "success", "response": response}, status=status.HTTP_200_OK)
    except KeyError as e:
        logger.error(f"KeyError in collection: {e}")
        return Response({"error": f"Key '{e}' not found in the response."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error in collection: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Collection callback handler
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def collection_callback(request):
    try:
        data = request.data
        callback = CollectionCallback(
            financial_transaction_id=data.get('financialTransactionId', ''),
            external_id=data.get('externalId', ''),
            amount=data.get('amount', 0),
            currency=data.get('currency', ''),
            party_id_type=data.get('payer', {}).get('partyIdType', ''),
            party_id=data.get('payer', {}).get('partyId', ''),
            payer_message=data.get('payerMessage', ''),
            payee_note=data.get('payeeNote', ''),
            status=data.get('status', ''),
        )
        callback.save()
        return Response({"status": "success"})
    except IntegrityError:
        logger.info("Duplicate callback received and ignored.")
        return Response({"status": "ignored"}, status=status.HTTP_200_OK)
    except KeyError as e:
        logger.error(f"KeyError in collection callback: {e}")
        return Response({"error": f"Key '{e}' not found in the callback data."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error in collection callback: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get collection callback by external_id
@api_view(['GET'])
@permission_classes([AllowAny])
def get_collection_callback(request):
    try:
        external_id = request.query_params.get('external_id')
        if not external_id:
            return Response({"error": "Missing 'external_id' parameter."}, status=status.HTTP_400_BAD_REQUEST)

        callback = get_object_or_404(CollectionCallback, external_id=external_id)
        callback_data = {
            'financial_transaction_id': callback.financial_transaction_id,
            'external_id': callback.external_id,
            'amount': callback.amount,
            'currency': callback.currency,
            'party_id_type': callback.party_id_type,
            'party_id': callback.party_id,
            'payer_message': callback.payer_message,
            'payee_note': callback.payee_note,
            'status': callback.status,
        }
        return Response({"status": "success", "callback": callback_data}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in get_collection_callback: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get all collection callbacks
@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_collection_callbacks(request):
    try:
        callbacks = CollectionCallback.objects.all()
        callback_list = [
            {
                'id': callback.id,
                'financial_transaction_id': callback.financial_transaction_id,
                'external_id': callback.external_id,
                'amount': callback.amount,
                'currency': callback.currency,
                'party_id_type': callback.party_id_type,
                'party_id': callback.party_id,
                'payer_message': callback.payer_message,
                'payee_note': callback.payee_note,
                'status': callback.status,
            } for callback in callbacks
        ]
        return Response({"status": "success", "callbacks": callback_list}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in get_all_collection_callbacks: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Edit a specific collection callback
@api_view(['PUT'])
@permission_classes([AllowAny])
def edit_collection_callback(request, id):
    try:
        callback = get_object_or_404(CollectionCallback, id=id)
        callback.financial_transaction_id = request.data.get('financial_transaction_id', callback.financial_transaction_id)
        callback.external_id = request.data.get('external_id', callback.external_id)
        callback.amount = request.data.get('amount', callback.amount)
        callback.currency = request.data.get('currency', callback.currency)
        callback.party_id_type = request.data.get('party_id_type', callback.party_id_type)
        callback.party_id = request.data.get('party_id', callback.party_id)
        callback.payer_message = request.data.get('payer_message', callback.payer_message)
        callback.payee_note = request.data.get('payee_note', callback.payee_note)
        callback.status = request.data.get('status', callback.status)
        callback.save()

        return Response({"status": "success", "callback": "Callback updated successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in edit_collection_callback: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Delete a specific collection callback
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_collection_callback(request, id):
    try:
        callback = get_object_or_404(CollectionCallback, id=id)
        callback.delete()

        return Response({"status": "success", "message": "Callback deleted successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in delete_collection_callback: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get a collection transaction by external_id
@api_view(['GET'])
@permission_classes([AllowAny])
def get_collection_transaction(request):
    try:
        external_id = request.query_params.get('external_id')
        if not external_id:
            return Response({"error": "Missing 'external_id' parameter."}, status=status.HTTP_400_BAD_REQUEST)

        transaction = get_object_or_404(CollectionTransaction, external_id=external_id)
        transaction_data = {
            'financial_transaction_id': transaction.financial_transaction_id,
            'external_id': transaction.external_id,
            'amount': transaction.amount,
            'currency': transaction.currency,
            'party_id_type': transaction.party_id_type,
            'party_id': transaction.party_id,
            'payer_message': transaction.payer_message,
            'payee_note': transaction.payee_note,
            'status': transaction.status,
        }
        return Response({"status": "success", "transaction": transaction_data}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in get_collection_transaction: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get all collection transactions
@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_collection_transactions(request):
    try:
        transactions = CollectionTransaction.objects.all()
        transaction_list = [
            {
                'id': transaction.id,
                'financial_transaction_id': transaction.financial_transaction_id,
                'external_id': transaction.external_id,
                'amount': transaction.amount,
                'currency': transaction.currency,
                'party_id_type': transaction.party_id_type,
                'party_id': transaction.party_id,
                'payer_message': transaction.payer_message,
                'payee_note': transaction.payee_note,
                'status': transaction.status,
            } for transaction in transactions
        ]
        return Response({"status": "success", "transactions": transaction_list}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in get_all_collection_transactions: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Edit a specific collection transaction
@api_view(['PUT'])
@permission_classes([AllowAny])
def edit_collection_transaction(request, id):
    try:
        transaction = get_object_or_404(CollectionTransaction, id=id)
        transaction.financial_transaction_id = request.data.get('financial_transaction_id', transaction.financial_transaction_id)
        transaction.external_id = request.data.get('external_id', transaction.external_id)
        transaction.amount = request.data.get('amount', transaction.amount)
        transaction.currency = request.data.get('currency', transaction.currency)
        transaction.party_id_type = request.data.get('party_id_type', transaction.party_id_type)
        transaction.party_id = request.data.get('party_id', transaction.party_id)
        transaction.payer_message = request.data.get('payer_message', transaction.payer_message)
        transaction.payee_note = request.data.get('payee_note', transaction.payee_note)
        transaction.status = request.data.get('status', transaction.status)
        transaction.save()

        return Response({"status": "success", "transaction": "Transaction updated successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in edit_collection_transaction: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Delete a specific collection transaction
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_collection_transaction(request, id):
    try:
        transaction = get_object_or_404(CollectionTransaction, id=id)
        transaction.delete()

        return Response({"status": "success", "message": "Transaction deleted successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in delete_collection_transaction: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)