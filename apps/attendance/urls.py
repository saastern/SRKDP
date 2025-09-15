from django.urls import path
from . import views

urlpatterns = [
    # Your existing API URLs
    path('api/class/<int:class_id>/students/', views.get_class_students, name='get_class_students'),
    path('api/attendance/report/', views.get_attendance_report, name='get_attendance_report'),
    path('api/attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('api/attendance/<int:class_id>/', views.get_attendance, name='get_attendance'),
    
    # ✅ ADD THIS LINE - handles /api/attendance/class/3/ calls
    path('api/attendance/class/<int:class_id>/', views.get_attendance, name='get_attendance_class'),
    
    # NEW: Summary API
    path('api/student/<int:student_id>/summary/', views.get_student_attendance_summary, name='student_summary'),
    
    # NEW: HTML Dashboard URLs
    path('dashboard/', views.attendance_dashboard, name='attendance_dashboard'),
    path('class/<int:class_id>/students/', views.class_students_summary, name='class_students_summary'),
    path('student/<int:student_id>/calendar/', views.student_calendar_view, name='student_calendar'),
]
