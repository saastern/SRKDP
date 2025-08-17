# apps/teachers/urls.py
from django.urls import path
from .views import teacher_dashboard

app_name = 'teachers'
urlpatterns = [
    path('dashboard/', teacher_dashboard, name='dashboard'),
]
