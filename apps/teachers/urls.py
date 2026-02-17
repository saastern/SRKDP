# apps/teachers/urls.py
from django.urls import path
from .views import teacher_dashboard, list_teachers

app_name = 'teachers'
urlpatterns = [
    path('dashboard/', teacher_dashboard, name='dashboard'),
    path('list/', list_teachers, name='list'),
]
