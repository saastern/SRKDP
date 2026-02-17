# apps/teachers/urls.py
from django.urls import path
from .views import teacher_dashboard, list_teachers, add_staff, update_staff, delete_staff

app_name = 'teachers'
urlpatterns = [
    path('dashboard/', teacher_dashboard, name='dashboard'),
    path('list/', list_teachers, name='list'),
    path('add/', add_staff, name='add_staff'),
    path('<int:staff_id>/update/', update_staff, name='update_staff'),
    path('<int:staff_id>/delete/', delete_staff, name='delete_staff'),
]
