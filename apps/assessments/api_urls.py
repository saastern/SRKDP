from django.urls import path
from .api_views import *
from .views import *

urlpatterns = [
    # Classes
    path('classes/', ClassListAPIView.as_view(), name='api-classes'),
    
    # Students
    path('students/', StudentListAPIView.as_view(), name='api-students'),
    path('student-marks/<str:student_id>/', StudentMarksDetailAPIView.as_view(), name='api-student-marks'),
    
    # Authentication
    path('auth/login/', teacher_login_api, name='api-teacher-login'),
]
