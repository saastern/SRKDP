from django.core.management.base import BaseCommand
from apps.assessments.models import *
from decimal import Decimal
from datetime import date

class Command(BaseCommand):
    help = 'Setup initial assessment data (exams, subjects, grades)'
    
    def handle(self, *args, **options):
        self.stdout.write("🚀 Setting up assessments data...")
        
        # 1. Create Academic Year
        self.create_academic_year()
        
        # 2. Create Default Exams
        self.create_exams()
        
        # 3. Create Subjects
        self.create_subjects()
        
        # 4. Create Grade Scales
        self.create_grade_scales()
        
        self.stdout.write(self.style.SUCCESS('✅ Assessment setup completed!'))
    
    def create_academic_year(self):
        academic_year, created = AcademicYear.objects.get_or_create(
            name="2024-2025",
            defaults={
                'start_date': date(2024, 6, 1),
                'end_date': date(2025, 5, 31),
                'is_current': True,
                'is_active': True
            }
        )
        if created:
            self.stdout.write("✓ Created academic year: 2024-2025")
        else:
            self.stdout.write("• Academic year 2024-2025 already exists")
    
    def create_exams(self):
        exams_data = [
            ('FA1', 'FA', 1),
            ('FA2', 'FA', 2), 
            ('FA3', 'FA', 3),
            ('FA4', 'FA', 4),
            ('SA1', 'SA', 1),
            ('SA2', 'SA', 2),
        ]
        
        for name, exam_type, order in exams_data:
            exam, created = Exam.objects.get_or_create(
                name=name,
                defaults={
                    'exam_type': exam_type,
                    'order': order,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f"✓ Created exam: {name}")
            else:
                # Update order for existing exam
                exam.order = order
                exam.exam_type = exam_type
                exam.save()
                self.stdout.write(f"• Updated exam: {name}")
    
    def create_subjects(self):
        subjects_data = [
            ('Telugu', 'TEL'),
            ('English', 'ENG'),
            ('Hindi', 'HIN'),
            ('Mathematics', 'MATH'),
            ('Color', 'COL'),
            ('EVS', 'EVS'),
            ('Science', 'SCI'),
            ('Social', 'SOC'),
            ('Physical Science', 'PHY'),
            ('Natural Science', 'NAT'),
            ('GK', 'GK'),
            ('Computer', 'COMP'),
        ]
        
        for name, code in subjects_data:
            subject, created = Subject.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f"✓ Created subject: {name}")
    
    def create_grade_scales(self):
        self.stdout.write("Creating grade scales...")
        
        # Grade data as per your specification
        grade_data = [
            # LKG-UKG (pre) - FA (50 marks max)
            ('pre', 'FA', 46, 50, 'A1', 10),
            ('pre', 'FA', 41, 45, 'A2', 9),
            ('pre', 'FA', 36, 40, 'B1', 8),
            ('pre', 'FA', 31, 35, 'B2', 7),
            ('pre', 'FA', 26, 30, 'C1', 6),
            ('pre', 'FA', 21, 25, 'C2', 5),
            ('pre', 'FA', 18, 20, 'D1', 4),
            ('pre', 'FA', 0, 17, 'D2', 3),
            
            # LKG-UKG (pre) - SA (100 marks max)
            ('pre', 'SA', 91, 100, 'A1', 10),
            ('pre', 'SA', 81, 90, 'A2', 9),
            ('pre', 'SA', 71, 80, 'B1', 8),
            ('pre', 'SA', 61, 70, 'B2', 7),
            ('pre', 'SA', 51, 60, 'C1', 6),
            ('pre', 'SA', 41, 50, 'C2', 5),
            ('pre', 'SA', 35, 40, 'D1', 4),
            ('pre', 'SA', 0, 34, 'D2', 3),
            
            # Classes 1-5 - FA (25 marks max)
            ('1-5', 'FA', 23, 25, 'A1', 10),
            ('1-5', 'FA', 21, 22, 'A2', 9),
            ('1-5', 'FA', 19, 20, 'B1', 8),
            ('1-5', 'FA', 17, 18, 'B2', 7),
            ('1-5', 'FA', 15, 16, 'C1', 6),
            ('1-5', 'FA', 13, 14, 'C2', 5),
            ('1-5', 'FA', 11, 12, 'D1', 4),
            ('1-5', 'FA', 0, 10, 'D2', 3),
            
            # Classes 1-5 - SA (100 marks max)
            ('1-5', 'SA', 91, 100, 'A1', 10),
            ('1-5', 'SA', 81, 90, 'A2', 9),
            ('1-5', 'SA', 71, 80, 'B1', 8),
            ('1-5', 'SA', 61, 70, 'B2', 7),
            ('1-5', 'SA', 51, 60, 'C1', 6),
            ('1-5', 'SA', 41, 50, 'C2', 5),
            ('1-5', 'SA', 35, 40, 'D1', 4),
            ('1-5', 'SA', 0, 34, 'D2', 3),
            
            # Classes 6-10 - FA (50 marks max)
            ('6-10', 'FA', 46, 50, 'A1', 10),
            ('6-10', 'FA', 41, 45, 'A2', 9),
            ('6-10', 'FA', 36, 40, 'B1', 8),
            ('6-10', 'FA', 31, 35, 'B2', 7),
            ('6-10', 'FA', 26, 30, 'C1', 6),
            ('6-10', 'FA', 21, 25, 'C2', 5),
            ('6-10', 'FA', 18, 20, 'D1', 4),
            ('6-10', 'FA', 0, 17, 'D2', 3),
            
            # Classes 6-10 - SA (100 marks max)
            ('6-10', 'SA', 91, 100, 'A1', 10),
            ('6-10', 'SA', 81, 90, 'A2', 9),
            ('6-10', 'SA', 71, 80, 'B1', 8),
            ('6-10', 'SA', 61, 70, 'B2', 7),
            ('6-10', 'SA', 51, 60, 'C1', 6),
            ('6-10', 'SA', 41, 50, 'C2', 5),
            ('6-10', 'SA', 35, 40, 'D1', 4),
            ('6-10', 'SA', 0, 34, 'D2', 3),
        ]
        
        created_count = 0
        for class_group, exam_type, min_marks, max_marks, grade, grade_point in grade_data:
            grade_scale, created = GradeScale.objects.get_or_create(
                class_group=class_group,
                exam_type=exam_type,
                min_marks=min_marks,
                max_marks=max_marks,
                defaults={
                    'grade': grade,
                    'grade_point': Decimal(str(grade_point))
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(f"✓ Created {created_count} grade scale entries")
