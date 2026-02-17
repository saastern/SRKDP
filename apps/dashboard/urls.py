from django.urls import path
from . import views

urlpatterns = [
    path('api/principal/summary/', views.principal_dashboard_summary, name='principal_dashboard_summary'),
]
