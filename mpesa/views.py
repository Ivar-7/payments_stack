from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import datetime
import base64
from requests.auth import HTTPBasicAuth
from decouple import config
import json
from .models import MpesaTransaction

def index(request):
    return render(request, 'mpesa/index.html')

@csrf_exempt
def mpesa_payment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        phone = data.get('phone')
        amount = data.get('amount')

        consumer_key = config('CONSUMER_KEY')
        consumer_secret = config('CONSUMER_SECRET')
        api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        data = r.json()
        access_token = "Bearer " + data['access_token']

        timestamp = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        passkey = config('PASSKEY')
        business_short_code = config('BUSINESS_SHORTCODE')
        data_to_encode = business_short_code + passkey + timestamp
        encoded = base64.b64encode(data_to_encode.encode())
        password = encoded.decode('utf-8')

        payload = {
            "BusinessShortCode": business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": business_short_code,
            "PhoneNumber": phone,
            "CallBackURL": "https://yourdomain.com/mpesa/callback",
            "AccountReference": "account",
            "TransactionDesc": "payment"
        }

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)
            response_data = response.json()
            return JsonResponse(response_data)
        except KeyError as e:
            return JsonResponse({"status": "error", "message": f"Key '{e}' not found in the response."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "error", "message": "Invalid request method."})

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        items = {}
        if 'CallbackMetadata' in data['Body']['stkCallback']:
            items = {item['Name']: item['Value'] for item in data['Body']['stkCallback']['CallbackMetadata']['Item']}

        MpesaTransaction.objects.create(
            merchant_request_id=data['Body']['stkCallback']['MerchantRequestID'],
            checkout_request_id=data['Body']['stkCallback']['CheckoutRequestID'],
            result_code=data['Body']['stkCallback']['ResultCode'],
            result_desc=data['Body']['stkCallback']['ResultDesc'],
            amount=items.get('Amount'),
            mpesa_receipt_number=items.get('MpesaReceiptNumber'),
            transaction_date=items.get('TransactionDate'),
            phone_number=items.get('PhoneNumber'),
        )

        return JsonResponse({'result_code': 0, 'result_desc': 'Success'})
    return JsonResponse({'result_code': 1, 'result_desc': 'Failed, not a POST request'})
