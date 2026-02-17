from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.principal_fee_dashboard, name='principal_fee_dashboard'),
    path('record-payment/', views.record_payment, name='record_payment'),
]
