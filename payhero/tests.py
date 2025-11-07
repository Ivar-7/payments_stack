from django.test import TestCase
from .serializers import InitiatePaymentSerializer, GlobalPaymentSerializer


class SerializerSmokeTests(TestCase):
	def test_initiate_payment_serializer_valid(self):
		data = {
			"amount": 100,
			"phone_number": "+254712345678",
			"channel_id": 1,
			"provider": "m-pesa",
		}
		ser = InitiatePaymentSerializer(data=data)
		self.assertTrue(ser.is_valid(), ser.errors)

	def test_global_payment_serializer_nested_valid(self):
		data = {
			"request_type": "payment",
			"provider": "m-pesa",
			"amount": "25.50",
			"currency": "KES",
			"country": "KE",
			"reference": "ref-123",
			"customer": {"phone": "+254700000000", "first_name": "A", "last_name": "B"},
			"provider_config": {"provider_id": "2031"},
			"vendor_config": {"vendor_id": "vnd-1", "channel_id": "chn-1"},
		}
		ser = GlobalPaymentSerializer(data=data)
		self.assertTrue(ser.is_valid(), ser.errors)
