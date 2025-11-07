from rest_framework import serializers

class TopupSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    phone_number = serializers.CharField(max_length=25)

class InitiatePaymentSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    phone_number = serializers.CharField(max_length=25)
    channel_id = serializers.IntegerField(min_value=1)
    provider = serializers.CharField(max_length=40)
    reference = serializers.CharField(max_length=120, required=False, allow_blank=True)
    external_reference = serializers.CharField(max_length=120, required=False, allow_blank=True)
    customer_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    callback_url = serializers.URLField(required=False, allow_blank=True)
    credential_id = serializers.CharField(max_length=120, required=False, allow_blank=True)
    network_code = serializers.CharField(max_length=10, required=False, allow_blank=True)

class WithdrawMobileSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    phone_number = serializers.CharField(max_length=25)
    network_code = serializers.CharField(max_length=10)
    channel_id = serializers.IntegerField(min_value=1)
    provider = serializers.CharField(max_length=40)
    external_reference = serializers.CharField(max_length=120, required=False, allow_blank=True)
    callback_url = serializers.URLField(required=False, allow_blank=True)

class TransactionsQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    per = serializers.IntegerField(min_value=1, required=False, default=20)

class TransactionStatusQuerySerializer(serializers.Serializer):
    reference = serializers.CharField(max_length=120)

class GlobalPaymentCustomerSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=25, required=False)
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(max_length=80, required=False)
    last_name = serializers.CharField(max_length=80, required=False)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)

class GlobalProviderConfigSerializer(serializers.Serializer):
    provider_id = serializers.CharField(max_length=40)
    merchant_id = serializers.CharField(max_length=80, required=False, allow_blank=True)
    category = serializers.CharField(max_length=80, required=False, allow_blank=True)

class GlobalVendorConfigSerializer(serializers.Serializer):
    vendor_id = serializers.CharField(max_length=80)
    channel_id = serializers.CharField(max_length=80)

class GlobalPaymentSerializer(serializers.Serializer):
    request_type = serializers.ChoiceField(choices=["topup", "payment", "withdrawal", "utility", "bills"])
    provider = serializers.CharField(max_length=40)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.CharField(max_length=10)
    country = serializers.CharField(max_length=5)
    reference = serializers.CharField(max_length=120)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    customer = GlobalPaymentCustomerSerializer()
    provider_config = GlobalProviderConfigSerializer()
    vendor_config = GlobalVendorConfigSerializer()
    callback_url = serializers.URLField(required=False, allow_blank=True)
    ipn_id = serializers.CharField(max_length=120, required=False, allow_blank=True)
