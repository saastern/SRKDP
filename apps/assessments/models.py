from django.db import models
from django.utils import timezone
from apps.students.models import StudentProfile, Class
from decimal import Decimal

class AcademicYear(models.Model):
    """Academic year like 2024-2025"""
    name = models.CharField(max_length=20, unique=True)  # "2024-2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    is_current = models.BooleanField(default=False)  # Only one can be current
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Ensure only one current academic year
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

class Subject(models.Model):
    """All subjects in the school"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class ClassSubjectMapping(models.Model):
    """Maps subjects to specific classes with main/optional designation"""
    student_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    is_main_subject = models.BooleanField(default=True)  # False for optional subjects
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['student_class', 'subject', 'academic_year']
        indexes = [
            models.Index(fields=['student_class', 'academic_year']),
        ]
    
    def __str__(self):
        subject_type = "Main" if self.is_main_subject else "Optional"
        return f"{self.student_class.name} - {self.subject.name} ({subject_type})"

class Exam(models.Model):
    """FA1-FA4, SA1-SA2 exams"""
    EXAM_TYPES = [
        ('FA', 'Formative Assessment'),
        ('SA', 'Summative Assessment')
    ]
    
    name = models.CharField(max_length=100, unique=True)  # FA1, FA2, SA1, SA2
    exam_type = models.CharField(max_length=2, choices=EXAM_TYPES)
    order = models.IntegerField()  # FA1=1, FA2=2, SA1=1, SA2=2
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['exam_type', 'order']
    
    def __str__(self):
        return self.name
    
    def get_max_marks(self, class_group):
        """Get max marks based on class group and exam type according to your spec"""
        if self.exam_type == 'SA':
            return 100  # SA is always 100 for all classes
        
        # FA max marks vary by class group as per your specification
        fa_max_marks = {
            'pre': 50,     # LKG-UKG: 50 marks
            '1-5': 25,     # Classes 1-5: 25 marks  
            '6-10': 50,    # Classes 6-10: 50 marks
        }
        return fa_max_marks.get(class_group, 50)

class GradeScale(models.Model):
    """Grading scales for different class groups and exam types as per your spec"""
    class_group = models.CharField(max_length=10)  # 'pre', '1-5', '6-10'
    exam_type = models.CharField(max_length=2)     # 'FA' or 'SA'
    min_marks = models.IntegerField()
    max_marks = models.IntegerField()
    grade = models.CharField(max_length=2)         # A1, A2, B1, etc.
    grade_point = models.DecimalField(max_digits=4, decimal_places=1)
    
    class Meta:
        unique_together = ['class_group', 'exam_type', 'min_marks', 'max_marks']
        ordering = ['class_group', 'exam_type', '-min_marks']
    
    def __str__(self):
        return f"{self.class_group}-{self.exam_type}: {self.min_marks}-{self.max_marks} = {self.grade} ({self.grade_point})"

class StudentMark(models.Model):
    """Individual marks for each student, subject, and exam"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.IntegerField()
    grade = models.CharField(max_length=2, blank=True)
    grade_point = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    
    is_absent = models.BooleanField(default=False)
    entered_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    entered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'subject', 'exam', 'academic_year']
        indexes = [
            models.Index(fields=['student', 'exam', 'academic_year']),
            models.Index(fields=['exam', 'academic_year']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate grade and grade point before saving
        if not self.is_absent and self.marks_obtained is not None:
            self.grade, self.grade_point = self.calculate_grade()
        elif self.is_absent:
            self.grade = 'AB'  # Absent
            self.grade_point = Decimal('0.0')
        super().save(*args, **kwargs)
    
    def calculate_grade(self):
        """Calculate grade based on marks and class group"""
        class_group = self.student.student_class.class_group
        
        try:
            # Find appropriate grade scale entry
            grade_scales = GradeScale.objects.filter(
                class_group=class_group,
                exam_type=self.exam.exam_type,
                min_marks__lte=self.marks_obtained,
                max_marks__gte=self.marks_obtained
            )
            
            grade_scale = grade_scales.first()
            if grade_scale:
                return grade_scale.grade, grade_scale.grade_point
                
        except Exception as e:
            print(f"Error calculating grade: {e}")
        
        # Default to lowest grade if no match found
        return 'D2', Decimal('3.0')
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.subject.name} - {self.exam.name}: {self.marks_obtained}/{self.max_marks} ({self.grade})"

class StudentExamSummary(models.Model):
    """Consolidated summary for each student's exam (e.g., FA1 total)"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    
    total_marks_obtained = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    total_max_marks = models.IntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_grade = models.CharField(max_length=2, blank=True)
    overall_grade_point = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    class_rank = models.IntegerField(null=True, blank=True)
    subjects_count = models.IntegerField(default=0)
    
    computed_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'exam', 'academic_year']
        indexes = [
            models.Index(fields=['exam', 'academic_year']),
        ]
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.exam.name}: {self.percentage}% (Rank: {self.class_rank})"
