from django.urls import path
from . import views

urlpatterns = [
    path('class/<int:class_id>/students/', views.get_class_students, name='get_class_students'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('class/<int:class_id>/', views.get_attendance, name='get_attendance'),
    path('report/', views.get_attendance_report, name='get_attendance_report'),  # Add this line
]
