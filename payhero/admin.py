from django.contrib import admin
from .models import PayHeroTransaction, PayHeroWebhookEvent


@admin.register(PayHeroTransaction)
class PayHeroTransactionAdmin(admin.ModelAdmin):
	list_display = ("reference", "amount", "currency", "status", "provider_txn_id", "created_at")
	search_fields = ("reference", "provider_txn_id", "phone_number")
	list_filter = ("status", "currency")


@admin.register(PayHeroWebhookEvent)
class PayHeroWebhookEventAdmin(admin.ModelAdmin):
	list_display = ("event_id", "topic", "received_at")
	search_fields = ("event_id", "topic")
