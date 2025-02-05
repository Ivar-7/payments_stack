from django.contrib import admin
from .models import CollectionTransaction, DisbursementTransaction, CollectionCallback, DisbursementCallback


admin.site.register(CollectionTransaction)
admin.site.register(DisbursementTransaction)

admin.site.register(CollectionCallback)
# class CollectionCallbackAdmin(admin.ModelAdmin):
#     list_display = ('financial_transaction_id', 'status', 'received_at')
#     search_fields = ('financial_transaction_id', 'external_id', 'status')

admin.site.register(DisbursementCallback)
# class DisbursementCallbackAdmin(admin.ModelAdmin):
#     list_display = ('ref', 'status', 'received_at')
#     search_fields = ('ref', 'external_id', 'status')