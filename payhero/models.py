from django.db import models


class PayHeroTransaction(models.Model):
	"""Stores a PayHero or Global transaction lifecycle for auditing and reconciliation.

	Adds provider/channel fields + last_status_payload to support richer status tracking.
	"""

	class Status(models.TextChoices):
		QUEUED = "QUEUED", "Queued"  # PayHero v2 / global queued state
		PENDING = "pending", "Pending"  # internal pending before provider ack
		PROCESSING = "processing", "Processing"
		SUCCESS = "SUCCESS", "Success"  # align with provider success tokens
		FAILED = "FAILED", "Failed"
		CANCELLED = "cancelled", "Cancelled"

	reference = models.CharField(max_length=120, unique=True, help_text="Internal unique reference")
	provider_txn_id = models.CharField(max_length=150, blank=True, null=True, help_text="ID returned by PayHero/provider")
	amount = models.DecimalField(max_digits=14, decimal_places=2)
	currency = models.CharField(max_length=10, default="KES")
	phone_number = models.CharField(max_length=25, blank=True, null=True)
	description = models.CharField(max_length=255, blank=True, null=True)
	provider = models.CharField(max_length=40, blank=True, null=True, help_text="e.g. m-pesa, sasapay, intasend")
	channel_id = models.IntegerField(blank=True, null=True, help_text="Wallet/payment channel identifier used")
	operation_type = models.CharField(max_length=30, blank=True, null=True, help_text="payment | topup | withdraw | global")
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	metadata = models.JSONField(default=dict, blank=True)
	last_status_payload = models.JSONField(default=dict, blank=True, help_text="Most recent raw status response")

	# Timestamps
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		indexes = [
			models.Index(fields=["reference"]),
			models.Index(fields=["provider_txn_id"]),
		]

	def __str__(self) -> str:  # pragma: no cover
		return f"{self.reference} - {self.status}"


class PayHeroWebhookEvent(models.Model):
	"""Stores raw webhook payloads for replay/forensics."""

	event_id = models.CharField(max_length=150, blank=True, null=True)
	signature = models.CharField(max_length=255, blank=True, null=True)
	topic = models.CharField(max_length=100, blank=True, null=True)
	raw_payload = models.JSONField()
	received_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:  # pragma: no cover
		return self.event_id or f"webhook-{self.pk}"
