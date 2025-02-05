from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging
import json
import uuid

from .models import DisbursementTransaction, DisbursementCallback
from .disbursement import Disbursement

logger = logging.getLogger(__name__)

# Utility functions to store disbursement transactions


def store_disbursement(response_data: dict) -> None:
    try:
        data = response_data.get('data', {})
        payee = data.get('payee', {})
        disbursement = DisbursementTransaction(
            response=response_data.get('response', ''),
            ref=response_data.get('ref', ''),
            amount=data.get('amount', 0),
            currency=data.get('currency', ''),
            financial_transaction_id=data.get('financialTransactionId', ''),
            external_id=data.get('externalId', ''),
            party_id_type=payee.get('partyIdType', ''),
            party_id=payee.get('partyId', ''),
            payer_message=data.get('payerMessage', ''),
            payee_note=data.get('payeeNote', ''),
            status=data.get('status', ''),
        )
        disbursement.save()
    except Exception as e:
        logger.error(f"Error storing disbursement transaction: {e}")
        raise

# Disbursement API with secure CSRF handling


@api_view(['POST'])
@permission_classes([AllowAny])
def disbursement(request):
    try:
        disbur = Disbursement()
        amount = request.data.get('amount')
        phone_number = request.data.get('phone')
        external_id = request.data.get('external_id')
        # Default to USD if not provided
        currency = request.data.get('currency', 'USD')

        # Initiate the disbursement request
        result = disbur.transfer(amount, phone_number, external_id, currency)

        if 'error' in result:
            return Response({"error": result['error']}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the transaction status and store it
        transfer_status_res = disbur.getTransactionStatus(
            result.get('ref', ''))
        store_disbursement(transfer_status_res)

        return Response({"status": "success", "response": result}, status=status.HTTP_200_OK)
    except KeyError as e:
        logger.error(f"KeyError in disbursement: {e}")
        return Response({"error": f"Key '{e}' not found in the response."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error in disbursement: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Disbursement callback handler


@api_view(['POST'])
@permission_classes([AllowAny])
def disbursement_callback(request):
    try:
        data = request.data
        callback = DisbursementCallback(
            response=data.get('response', ''),
            ref=data.get('ref', ''),
            amount=data.get('data', {}).get('amount', 0),
            currency=data.get('data', {}).get('currency', ''),
            financial_transaction_id=data.get(
                'data', {}).get('financialTransactionId', ''),
            external_id=data.get('data', {}).get('externalId', ''),
            party_id_type=data.get('data', {}).get(
                'payee', {}).get('partyIdType', ''),
            party_id=data.get('data', {}).get('payee', {}).get('partyId', ''),
            payer_message=data.get('data', {}).get('payerMessage', ''),
            payee_note=data.get('data', {}).get('payeeNote', ''),
            status=data.get('data', {}).get('status', ''),
        )
        callback.save()
        return Response({"status": "success"})
    except KeyError as e:
        logger.error(f"KeyError in disbursement callback: {e}")
        return Response({"error": f"Key '{e}' not found in the callback data."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error in disbursement callback: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get disbursement callback by external_id


@api_view(['GET'])
@permission_classes([AllowAny])
def get_disbursement_callback(request):
    try:
        external_id = request.query_params.get('external_id')
        if not external_id:
            return Response({"error": "Missing 'external_id' parameter."}, status=status.HTTP_400_BAD_REQUEST)

        callback = get_object_or_404(
            DisbursementCallback, external_id=external_id)
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
        logger.error(f"Unexpected error in get_disbursement_callback: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get all disbursement callbacks


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_disbursement_callbacks(request):
    try:
        callbacks = DisbursementCallback.objects.all()
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
        logger.error(
            f"Unexpected error in get_all_disbursement_callbacks: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Edit a specific disbursement callback


@api_view(['PUT'])
@permission_classes([AllowAny])
def edit_disbursement_callback(request, id):
    try:
        callback = get_object_or_404(DisbursementCallback, id=id)
        callback.financial_transaction_id = request.data.get(
            'financial_transaction_id', callback.financial_transaction_id)
        callback.external_id = request.data.get(
            'external_id', callback.external_id)
        callback.amount = request.data.get('amount', callback.amount)
        callback.currency = request.data.get('currency', callback.currency)
        callback.party_id_type = request.data.get(
            'party_id_type', callback.party_id_type)
        callback.party_id = request.data.get('party_id', callback.party_id)
        callback.payer_message = request.data.get(
            'payer_message', callback.payer_message)
        callback.payee_note = request.data.get(
            'payee_note', callback.payee_note)
        callback.status = request.data.get('status', callback.status)
        callback.save()

        return Response({"status": "success", "callback": "Callback updated successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in edit_disbursement_callback: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Delete a specific disbursement callback


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_disbursement_callback(request, id):
    try:
        callback = get_object_or_404(DisbursementCallback, id=id)
        callback.delete()

        return Response({"status": "success", "message": "Callback deleted successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in delete_disbursement_callback: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get a disbursement transaction by external_id


@api_view(['GET'])
@permission_classes([AllowAny])
def get_disbursement_transaction(request):
    try:
        external_id = request.query_params.get('external_id')
        if not external_id:
            return Response({"error": "Missing 'external_id' parameter."}, status=status.HTTP_400_BAD_REQUEST)

        transaction = get_object_or_404(
            DisbursementTransaction, external_id=external_id)
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
        logger.error(f"Unexpected error in get_disbursement_transaction: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get all disbursement transactions


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_disbursement_transactions(request):
    try:
        transactions = DisbursementTransaction.objects.all()
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
        logger.error(
            f"Unexpected error in get_all_disbursement_transactions: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Edit a specific disbursement transaction


@api_view(['PUT'])
@permission_classes([AllowAny])
def edit_disbursement_transaction(request, id):
    try:
        transaction = get_object_or_404(DisbursementTransaction, id=id)
        transaction.financial_transaction_id = request.data.get(
            'financial_transaction_id', transaction.financial_transaction_id)
        transaction.external_id = request.data.get(
            'external_id', transaction.external_id)
        transaction.amount = request.data.get('amount', transaction.amount)
        transaction.currency = request.data.get(
            'currency', transaction.currency)
        transaction.party_id_type = request.data.get(
            'party_id_type', transaction.party_id_type)
        transaction.party_id = request.data.get(
            'party_id', transaction.party_id)
        transaction.payer_message = request.data.get(
            'payer_message', transaction.payer_message)
        transaction.payee_note = request.data.get(
            'payee_note', transaction.payee_note)
        transaction.status = request.data.get('status', transaction.status)
        transaction.save()

        return Response({"status": "success", "transaction": "Transaction updated successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in edit_disbursement_transaction: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Delete a specific disbursement transaction


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_disbursement_transaction(request, id):
    try:
        transaction = get_object_or_404(DisbursementTransaction, id=id)
        transaction.delete()

        return Response({"status": "success", "message": "Transaction deleted successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(
            f"Unexpected error in delete_disbursement_transaction: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
