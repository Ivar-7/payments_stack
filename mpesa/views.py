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
    return render(request, 'index.html')

@csrf_exempt
def mpesa_payment(request):
    if request.method == 'POST':
        print("Received M-Pesa payment request")
        # Handle form submission
        if request.content_type == 'application/json':
            # API call (JSON data)
            data = json.loads(request.body)
            phone = data.get('phone')
            amount = data.get('amount')
        else:
            # Form submission (form data)
            phone = request.POST.get('phone')
            amount = request.POST.get('amount')

        # print(f"Phone: {phone}, Amount: {amount}")
        # print(f"Request content type: {request.content_type}")
        # print(f"Request POST data: {request.POST}")

        # Validate phone number format
        if not phone or not phone.startswith('254') or len(phone) != 12:
            error_response = {
                "ResponseCode": "1",
                "ResponseDescription": "Invalid phone number. Use format 254XXXXXXXXX",
                "errorMessage": "Phone number must be in format 254XXXXXXXXX"
            }
            if request.content_type != 'application/json':
                return render(request, 'index.html', {'response': error_response})
            return JsonResponse(error_response)

        # Validate amount
        try:
            amount_int = int(amount)
            if amount_int < 1:
                raise ValueError("Amount must be at least 1")
        except (ValueError, TypeError):
            error_response = {
                "ResponseCode": "1",
                "ResponseDescription": "Invalid amount. Must be a positive number",
                "errorMessage": "Amount must be a positive number"
            }
            if request.content_type != 'application/json':
                return render(request, 'index.html', {'response': error_response})
            return JsonResponse(error_response)

        consumer_key = config('CONSUMER_KEY')
        consumer_secret = config('CONSUMER_SECRET')
        api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        
        try:
            r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
            token_data = r.json()
            access_token = "Bearer " + token_data['access_token']
            # print(f"Access Token: {access_token}")

            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
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
                "CallBackURL": "https://skyfield-app-wuuco.ondigitalocean.app/mpesa/mpesa_callback/",
                "AccountReference": "Test",
                "TransactionDesc": "Test"
            }

            headers = {
                "Authorization": access_token,
                "Content-Type": "application/json"
            }

            # print(f"Payload: {payload}")

            response = requests.post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)
            response_data = response.json()
            # print(f"M-Pesa API Response: {response_data}")
            
            # For form submissions, render template with response
            if request.content_type != 'application/json':
                # Add formatted response for debug display
                response_data['debug_json'] = json.dumps(response_data, indent=2)
                # print(f"Rendering template with response: {response_data}")
                return render(request, 'index.html', {'response': response_data})
            
            # For API calls, return JSON
            return JsonResponse(response_data)
            
        except requests.exceptions.RequestException as e:
            error_response = {
                "ResponseCode": "1", 
                "ResponseDescription": f"Network error: {str(e)}",
                "errorMessage": "Failed to connect to M-Pesa API"
            }
            if request.content_type != 'application/json':
                return render(request, 'index.html', {'response': error_response})
            return JsonResponse(error_response)
        except json.JSONDecodeError as e:
            error_response = {
                "ResponseCode": "1",
                "ResponseDescription": "Invalid response from M-Pesa API", 
                "errorMessage": "Could not parse API response"
            }
            if request.content_type != 'application/json':
                return render(request, 'index.html', {'response': error_response})
            return JsonResponse(error_response)
        except KeyError as e:
            error_response = {
                "ResponseCode": "1",
                "ResponseDescription": f"Missing key in API response: {str(e)}",
                "errorMessage": f"Key '{e}' not found in the response."
            }
            if request.content_type != 'application/json':
                return render(request, 'index.html', {'response': error_response})
            return JsonResponse(error_response)
        except Exception as e:
            error_response = {
                "ResponseCode": "1",
                "ResponseDescription": f"Unexpected error: {str(e)}",
                "errorMessage": str(e)
            }
            if request.content_type != 'application/json':
                return render(request, 'index.html', {'response': error_response})
            return JsonResponse(error_response)
    
    # Handle GET request - show the form
    return render(request, 'index.html')

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
