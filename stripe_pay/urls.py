from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('config/', views.stripe_config, name='config'),
    path('create-checkout-session/', views.create_checkout_session),
    path('success/', views.success, name='success'),
    path('cancelled/', views.cancelled, name='cancelled'),
    path('webhook/', views.stripe_webhook, name='webhook'),
]