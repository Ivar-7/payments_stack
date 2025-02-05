import requests
import json
import uuid
import time
import base64
from requests.exceptions import RequestException


class Collection:
    def __init__(self):
        self.collections_primary_key = 'fe4f90ededed41eca438ff3f4d20ac4c'
        self.api_key = '79f14ddd6bdc4d5dbf559bd0d0e1c497'
        self.api_user = '22a08097-1b1b-479c-9a05-99eb0b3c1ad2'
        self.environment = 'mtnliberia'
        self.callback_host = 'https://teeket-payments-e225a1f9edcf.herokuapp.com/mtnmo/collection/callback/'
        self.base_url = 'https://proxy.momoapi.mtn.com'
        self.auth_token = None  # Store token to reuse it
        self.token_expiry = None  # Track when token expires
        
        # If sandbox environment, use the sandbox URL
        if self.environment == "sandbox":
            self.base_url = "https://sandbox.momodeveloper.mtn.com"
            self.api_user = str(uuid.uuid4())  # Auto-generate user in sandbox mode

        # Create API user
        self.create_api_user()
        # Create API key
        self.create_api_key()

        # Create basic auth key for Collections
        self.username, self.password = self.api_user, self.api_key
        self.basic_authorisation_collections = base64.b64encode(
            f"{self.username}:{self.password}".encode()
        ).decode()

    def create_api_user(self):
        url = f"{self.base_url}/v1_0/apiuser"
        payload = json.dumps({
            "providerCallbackHost": self.callback_host
        })
        headers = {
            'X-Reference-Id': self.api_user,
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.collections_primary_key
        }
        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()  # Raise an error for non-200 responses
        except RequestException as e:
            print(f"Error creating API user: {str(e)}")

    def create_api_key(self):
        url = f"{self.base_url}/v1_0/apiuser/{self.api_user}/apikey"
        headers = {
            'Ocp-Apim-Subscription-Key': self.collections_primary_key
        }
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            # Auto-generate key in sandbox mode
            if self.environment == "sandbox":
                self.api_key = response_data.get("apiKey", None)
                if not self.api_key:
                    print("Error: API key not found in response")
        except RequestException as e:
            print(f"Error creating API key: {str(e)}")

    def authToken(self):
        # Check if we have a valid token and it's not expired
        if self.auth_token and self.token_expiry and self.token_expiry > time.time():
            return self.auth_token

        url = f"{self.base_url}/collection/token/"
        headers = {
            'Ocp-Apim-Subscription-Key': self.collections_primary_key,
            'Authorization': f"Basic {self.basic_authorisation_collections}"
        }
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            token_data = response.json()
            self.auth_token = token_data.get("access_token", None)
            expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour if not specified
            self.token_expiry = time.time() + expires_in

            if not self.auth_token:
                print("Error: Access token not found in response")
                return None
            return self.auth_token

        except RequestException as e:
            print(f"Error obtaining auth token: {str(e)}")
            return None

    def requestToPay(self, amount, phone_number, external_id, currency, payernote="Teeket", payermessage="Ticket Purchase"):
        uuidgen = str(uuid.uuid4())
        url = f"{self.base_url}/collection/v1_0/requesttopay"
        payload = json.dumps({
            "amount": amount,
            "currency": currency,
            "externalId": external_id,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone_number
            },
            "payerMessage": payermessage,
            "payeeNote": payernote
        })
        headers = {
            'X-Reference-Id': uuidgen,
            'X-Target-Environment': self.environment,
            'X-Callback-Url': self.callback_host,
            'Ocp-Apim-Subscription-Key': self.collections_primary_key,
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.authToken()}"
        }

        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            return {"status_code": response.status_code, "ref": uuidgen}
        except RequestException as e:
            print(f"Error requesting payment: {str(e)}")
            return {"error": str(e)}

    def getTransactionStatus(self, txn):
        url = f"{self.base_url}/collection/v1_0/requesttopay/{txn}"
        headers = {
            'Ocp-Apim-Subscription-Key': self.collections_primary_key,
            'Authorization': f"Bearer {self.authToken()}",
            'X-Target-Environment': self.environment,
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"Error getting transaction status: {str(e)}")
            return {"error": str(e)}

    def getBalance(self):
        url = f"{self.base_url}/collection/v1_0/account/balance"
        headers = {
            'Ocp-Apim-Subscription-Key': self.collections_primary_key,
            'Authorization': f"Bearer {self.authToken()}",
            'X-Target-Environment': self.environment,
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"Error getting balance: {str(e)}")
            return {"error": str(e)}
