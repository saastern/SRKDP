from django.urls import path
from . import views

urlpatterns = [
    path('api/principal/fee-dashboard/', views.principal_fee_dashboard, name='fee_dashboard'),
]
