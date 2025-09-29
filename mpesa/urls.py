"""
M-Pesa URL patterns - Clean consolidated version
"""
from django.urls import path
from . import views

urlpatterns = [
    # Main page
    path('', views.index, name='index'),
    
    # Payment endpoints
    path('stk-push/', views.stk_push_payment, name='stk_push_payment'),
    path('send-money/', views.send_money, name='send_money'),
    path('payment-status/', views.payment_status, name='payment_status'),
    
    # Transaction management
    path('transactions/', views.user_transactions, name='user_transactions'),
    path('transactions/summary/', views.transaction_summary, name='transaction_summary'),
    
    # Callback endpoints (Safaricom webhooks)
    path('stk-callback/', views.mpesa_callback, name='stk_callback'),
    path('b2c-result/', views.b2c_result_callback, name='b2c_result_callback'),
    path('b2c-timeout/', views.b2c_timeout_callback, name='b2c_timeout_callback'),
]