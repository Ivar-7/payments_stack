from django.db import models

class MpesaTransaction(models.Model):
    merchant_request_id = models.CharField(max_length=50)
    checkout_request_id = models.CharField(max_length=50)
    result_code = models.IntegerField()
    result_desc = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    transaction_date = models.BigIntegerField(null=True, blank=True)
    phone_number = models.CharField(max_length=14, null=True, blank=True)

    def __str__(self):
        return self.merchant_request_id