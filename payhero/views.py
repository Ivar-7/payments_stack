from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .services.payment_service import PaymentService
from .models import PayHeroTransaction, PayHeroWebhookEvent
from .serializers import (
	TopupSerializer,
	InitiatePaymentSerializer,
	WithdrawMobileSerializer,
	TransactionsQuerySerializer,
	TransactionStatusQuerySerializer,
	GlobalPaymentSerializer,
)
from .http import safe_call, error_payload


class ServiceWalletBalanceView(APIView):
	def get(self, request):
		service = PaymentService()
		return safe_call(lambda: service.get_service_wallet_balance())


class PaymentChannelBalanceView(APIView):
	def get(self, request, channel_id: int):
		service = PaymentService()
		return safe_call(lambda: service.get_payment_channel_balance(channel_id))


class TopupServiceWalletView(APIView):
	def post(self, request):
		serializer = TopupSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = PaymentService()
		return safe_call(lambda: service.topup_service_wallet(**serializer.validated_data), status_code=status.HTTP_201_CREATED)


class InitiatePaymentView(APIView):
	"""Initiate a v2 MPESA/SasaPay payment."""

	def post(self, request):
		serializer = InitiatePaymentSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = PaymentService()
		return safe_call(lambda: service.initiate_payment(**serializer.validated_data), status_code=status.HTTP_201_CREATED)


class WithdrawMobileView(APIView):
	def post(self, request):
		serializer = WithdrawMobileSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = PaymentService()
		return safe_call(lambda: service.withdraw_mobile(**serializer.validated_data), status_code=status.HTTP_201_CREATED)


class TransactionsListView(APIView):
	def get(self, request):
		serializer = TransactionsQuerySerializer(data=request.query_params)
		serializer.is_valid(raise_exception=True)
		service = PaymentService()
		return safe_call(lambda: service.list_transactions(**serializer.validated_data))


class TransactionStatusView(APIView):
	def get(self, request):
		serializer = TransactionStatusQuerySerializer(data=request.query_params)
		serializer.is_valid(raise_exception=True)
		try:
			service = PaymentService()
			status_payload = service.fetch_status(serializer.validated_data["reference"])
			return Response(status_payload)
		except PayHeroTransaction.DoesNotExist:
			return Response({"detail": "Unknown reference"}, status=404)
		except Exception as e:  # noqa: BLE001
			from .http import handle_exception
			return handle_exception(e)


class GlobalDiscoveryView(APIView):
	def get(self, request):
		country = request.query_params.get("country", "KE")
		service = PaymentService()
		return safe_call(lambda: service.global_discovery(country=country))


class GlobalPaymentView(APIView):
	def post(self, request):
		serializer = GlobalPaymentSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		service = PaymentService()
		return safe_call(lambda: service.global_payment(**serializer.validated_data), status_code=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookReceiverView(APIView):
	"""Receive PayHero webhooks (signature verification to be added when spec provided)."""

	def post(self, request):
		payload = request.data
		# TODO: verify signature header when provider docs supplied
		def _save():
			return {"status": "accepted", "event_id": PayHeroWebhookEvent.objects.create(raw_payload=payload).pk}
		return safe_call(_save, status_code=200)
