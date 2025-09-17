from django.test import TestCase
from .models import *
from .services import GradingService
from apps.students.models import StudentProfile, Class
from apps.users.models import User

class AssessmentTestCase(TestCase):
    def setUp(self):
        # Create test data
        self.academic_year = AcademicYear.objects.create(
            name="2024-2025",
            start_date="2024-06-01",
            end_date="2025-05-31",
            is_current=True
        )
        
        self.exam = Exam.objects.create(
            name="FA1",
            exam_type="FA",
            order=1
        )
        
        self.subject = Subject.objects.create(
            name="Mathematics",
            code="MATH"
        )
    
    def test_grade_calculation(self):
        """Test grade calculation from marks"""
        # This will test our grading system
        grade, gp = GradingService.get_grade_from_percentage(85, '1-5', 'FA')
        self.assertIsNotNone(grade)
        print(f"Grade for 85% in 1-5 FA: {grade} (GP: {gp})")
