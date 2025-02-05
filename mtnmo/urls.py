from django.urls import path
from . import views, collection_views, disbursement_views

urlpatterns = [
    # Views
    path('', views.index, name='index'),
    path('csrf-token/', views.get_csrf_token, name='csrf_token'),

    # Collection URLs
    path('collect/', collection_views.collection, name='collect'),
    path('collection/callback/', collection_views.collection_callback, name='collection_callback'),
    path('collection/callback/<int:id>/', collection_views.edit_collection_callback, name='edit_collection_callback'),
    path('collection/callback/<int:id>/delete/', collection_views.delete_collection_callback, name='delete_collection_callback'),
    path('collection/callbacks/', collection_views.get_all_collection_callbacks, name='get_all_collection_callbacks'),
    path('get_collection_callback/', collection_views.get_collection_callback, name='get_collection_callback'),
    path('collection/transaction/', collection_views.get_collection_transaction, name='get_collection_transaction'),
    path('collection/transactions/', collection_views.get_all_collection_transactions, name='get_all_collection_transactions'),
    path('collection/transaction/<int:id>/', collection_views.edit_collection_transaction, name='edit_collection_transaction'),
    path('collection/transaction/<int:id>/delete/', collection_views.delete_collection_transaction, name='delete_collection_transaction'),

    # Disbursement URLs
    path('disburse/', disbursement_views.disbursement, name='disburse'),
    path('disbursement/callback/', disbursement_views.disbursement_callback, name='disbursement_callback'),
    path('disbursement/callback/<int:id>/', disbursement_views.edit_disbursement_callback, name='edit_disbursement_callback'),
    path('disbursement/callback/<int:id>/delete/', disbursement_views.delete_disbursement_callback, name='delete_disbursement_callback'),
    path('disbursement/callbacks/', disbursement_views.get_all_disbursement_callbacks, name='get_all_disbursement_callbacks'),
    path('disbursement/get_callback/', disbursement_views.get_disbursement_callback, name='get_disbursement_callback'),
    path('disbursement/transaction/', disbursement_views.get_disbursement_transaction, name='get_disbursement_transaction'),
    path('disbursement/transactions/', disbursement_views.get_all_disbursement_transactions, name='get_all_disbursement_transactions'),
    path('disbursement/transaction/<int:id>/', disbursement_views.edit_disbursement_transaction, name='edit_disbursement_transaction'),
    path('disbursement/transaction/<int:id>/delete/', disbursement_views.delete_disbursement_transaction, name='delete_disbursement_transaction'),
]