from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('mpesa_payment/', views.mpesa_payment, name='mpesa_payment'),
    path('mpesa_callback/', views.mpesa_callback, name='mpesa_callback'),
]