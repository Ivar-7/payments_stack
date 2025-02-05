import json
import requests
import uuid
import time
import base64
from requests.exceptions import RequestException

class Disbursement:
    def __init__(self):
        self.disbursements_primary_key = '6ca46276a5564541a814ef94f364c102'
        self.api_key_disbursements = 'ccb60945094a4b21a540f4ed49f09233'
        self.disbursements_apiuser = '5da52180-5ff2-4090-a6b3-ac194b920fcf'
        self.environment_mode = 'mtnliberia'
        self.callback_url = 'https://teeket-payments-e225a1f9edcf.herokuapp.com/mtnmo/disbursement/callback/'
        self.base_url = 'https://proxy.momoapi.mtn.com'
        self.auth_token = None
        self.token_expiry = None

        if self.environment_mode == "sandbox":
            self.base_url = "https://sandbox.momodeveloper.mtn.com"
            self.disbursements_apiuser = str(uuid.uuid4())

        self.create_api_user()
        self.create_api_key()

        self.username, self.password = self.disbursements_apiuser, self.api_key_disbursements
        self.basic_authorisation_disbursements = base64.b64encode(
            f"{self.username}:{self.password}".encode()
        ).decode()

    def create_api_user(self):
        url = f"{self.base_url}/v1_0/apiuser"
        payload = json.dumps({
            "providerCallbackHost": self.callback_url
        })
        headers = {
            'X-Reference-Id': self.disbursements_apiuser,
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.disbursements_primary_key
        }
        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
        except RequestException as e:
            print(f"Error creating API user: {str(e)}")

    def create_api_key(self):
        url = f"{self.base_url}/v1_0/apiuser/{self.disbursements_apiuser}/apikey"
        headers = {
            'Ocp-Apim-Subscription-Key': self.disbursements_primary_key
        }
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            if self.environment_mode == "sandbox":
                self.api_key_disbursements = response_data.get("apiKey", None)
                if not self.api_key_disbursements:
                    print("Error: API key not found in response")
        except RequestException as e:
            print(f"Error creating API key: {str(e)}")

    def authToken(self):
        if self.auth_token and self.token_expiry and self.token_expiry > time.time():
            return self.auth_token

        url = f"{self.base_url}/disbursement/token/"
        headers = {
            'Ocp-Apim-Subscription-Key': self.disbursements_primary_key,
            'Authorization': f"Basic {self.basic_authorisation_disbursements}"
        }
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            token_data = response.json()
            self.auth_token = token_data.get("access_token", None)
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = time.time() + expires_in

            if not self.auth_token:
                print("Error: Access token not found in response")
                return None
            return self.auth_token
        except RequestException as e:
            print(f"Error obtaining auth token: {str(e)}")
            return None

    def getBalance(self):
        url = f"{self.base_url}/disbursement/v1_0/account/balance"
        headers = {
            'Ocp-Apim-Subscription-Key': self.disbursements_primary_key,
            'Authorization': f"Bearer {self.authToken()}",
            'X-Target-Environment': self.environment_mode,
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"Error getting balance: {str(e)}")
            return {"error": str(e)}

    def transfer(self, amount, phone_number, external_id, currency="USD", payermessage="Teeket disbursement", payernote="Teeket"):
        uuidgen = str(uuid.uuid4())
        url = f"{self.base_url}/disbursement/v1_0/transfer"
        payload = json.dumps({
            "amount": amount,
            "currency": currency,
            "externalId": external_id,
            "payee": {
                "partyIdType": "MSISDN",
                "partyId": phone_number
            },
            "payerMessage": payermessage,
            "payeeNote": payernote
        })
        headers = {
            'X-Reference-Id': uuidgen,
            'X-Target-Environment': self.environment_mode,
            'X-Callback-Url': self.callback_url,
            'Ocp-Apim-Subscription-Key': self.disbursements_primary_key,
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.authToken()}"
        }
        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            return {"response": response.status_code, "ref": uuidgen}
        except RequestException as e:
            print(f"Error requesting transfer: {str(e)}")
            return {"error": str(e)}

    def getTransactionStatus(self, txn_ref):
        url = f"{self.base_url}/disbursement/v1_0/transfer/{txn_ref}"
        headers = {
            'Ocp-Apim-Subscription-Key': self.disbursements_primary_key,
            'Authorization': f"Bearer {self.authToken()}",
            'X-Target-Environment': self.environment_mode
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            returneddata = response.json()
            return {
                "response": response.status_code,
                "ref": txn_ref,
                "data": returneddata
            }
        except RequestException as e:
            print(f"Error getting transaction status: {str(e)}")
            return {"error": str(e)}