from django.db import models

class CollectionTransaction(models.Model):
    financial_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    external_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, blank=True, null=True)
    party_id_type = models.CharField(max_length=50, blank=True, null=True)
    party_id = models.CharField(max_length=50, blank=True, null=True)
    payer_message = models.TextField(blank=True, null=True)
    payee_note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)

class DisbursementTransaction(models.Model):
    response = models.IntegerField(blank=True, null=True)
    ref = models.UUIDField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, blank=True, null=True)
    financial_transaction_id = models.CharField(max_length=100)
    external_id = models.CharField(max_length=100)
    party_id_type = models.CharField(max_length=50, blank=True, null=True)
    party_id = models.CharField(max_length=50)
    payer_message = models.CharField(max_length=100, blank=True, null=True)
    payee_note = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50)

class CollectionCallback(models.Model):
    financial_transaction_id = models.CharField(max_length=255)
    external_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    party_id_type = models.CharField(max_length=50)
    party_id = models.CharField(max_length=255)
    payer_message = models.TextField(blank=True)
    payee_note = models.TextField(blank=True)
    status = models.CharField(max_length=50)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.financial_transaction_id} - {self.status}"

class DisbursementCallback(models.Model):
    response = models.CharField(max_length=255)
    ref = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    financial_transaction_id = models.CharField(max_length=255)
    external_id = models.CharField(max_length=255)
    party_id_type = models.CharField(max_length=50)
    party_id = models.CharField(max_length=255)
    payer_message = models.TextField(blank=True)
    payee_note = models.TextField(blank=True)
    status = models.CharField(max_length=50)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ref} - {self.status}"
