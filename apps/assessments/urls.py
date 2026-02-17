from django.urls import path
from . import api_views
from . import views
from django.urls import include

urlpatterns = [
    # Get form data
    path('marks/form-data/', api_views.get_marks_entry_form_data, name='marks_form_data'),
    
    # Enter marks
    path('marks/enter/', api_views.enter_marks, name='enter_marks'),
    
    # Get dropdowns data
    path('classes/', views.ClassListAPIView.as_view(), name='class_list'),
    path('students/', views.StudentListAPIView.as_view(), name='student_list'),
    path('subjects/', views.SubjectListAPIView.as_view(), name='subject_list'),
    path('exams/', views.ExamListAPIView.as_view(), name='exam_list'),
    path('marks/', views.save_marks_sheet, name='save_marks'),
    path('class-results/', views.get_class_results, name='class_results'),
    path('init-class-orders/', views.initialize_class_orders, name='init_class_orders'),
    path('', include('apps.assessments.api_urls')),
]
