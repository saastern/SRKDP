from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.principal_fee_dashboard, name='principal_fee_dashboard'),
    path('transactions/', views.list_transactions, name='list_transactions'),
    path('transactions/<int:tx_id>/', views.delete_transaction, name='delete_transaction'),
    path('student-status/', views.get_student_fee_status, name='student_fee_status'),
    path('record-payment/', views.record_payment, name='record_payment'),
]
