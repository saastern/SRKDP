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
    path('data/', api_views.get_classes_and_exams, name='classes_exams'),
    path('marks/student/<str:student_id>/exam/<int:exam_id>/', api_views.get_student_marks, name='get_student_marks'),
    path('marks-entry-sheet/', views.marks_entry_sheet, name='marks_entry_sheet'),
    path('marks-sheet-data/', views.get_marks_sheet_data, name='marks_sheet_data'),
    path('save-marks-sheet/', views.save_marks_sheet, name='save_marks_sheet'),
    path('', include('apps.assessments.api_urls')),
]
