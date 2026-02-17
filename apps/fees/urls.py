from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.principal_fee_dashboard, name='fee_dashboard'),
    path('student-status/', views.get_student_fee_status, name='student_fee_status'),
    path('record-payment/', views.record_payment, name='record_payment'),
]
