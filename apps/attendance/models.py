from django.db import models
from django.utils import timezone
from apps.students.models import StudentProfile
from datetime import datetime, timedelta

# Custom Manager (keep this)
class AttendanceRecordManager(models.Manager):
    def get_student_attendance(self, student, start_date, end_date):
        """Get all attendance records for a student in date range"""
        return self.filter(
            student=student,
            session__date__gte=start_date,
            session__date__lte=end_date
        ).select_related('session')
    
    def get_daily_attendance(self, student, date):
        """Get both morning and afternoon attendance for a specific date"""
        records = self.filter(
            student=student,
            session__date=date
        ).select_related('session')
        
        result = {'morning': None, 'afternoon': None}
        for record in records:
            result[record.session.session] = record.status
        
        return result

class AttendanceSession(models.Model):
    SESSION_CHOICES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
    ]
    
    date = models.DateField()
    session = models.CharField(max_length=10, choices=SESSION_CHOICES)
    student_class = models.ForeignKey('students.Class', on_delete=models.CASCADE)
    teacher = models.ForeignKey('users.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['date', 'session', 'student_class']
    
    def __str__(self):
        return f"{self.student_class.name} - {self.date} ({self.session})"

class AttendanceRecord(models.Model):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    is_present = models.BooleanField(default=True)
    marked_at = models.DateTimeField(auto_now=True)
    
    # Direct manager assignment (PREFERRED)
    objects = AttendanceRecordManager()
    
    class Meta:
        unique_together = ['session', 'student']
    
    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student.user.first_name} {self.student.user.last_name} - {status}"
    
    @property
    def status(self):
        return "PRESENT" if self.is_present else "ABSENT"

class AttendanceSummary(models.Model):
    """Computed attendance summary for performance"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    total_school_days = models.IntegerField(default=0)
    full_present_days = models.IntegerField(default=0)
    half_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    computed_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'year', 'month']
        indexes = [
            models.Index(fields=['student', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.student} - {self.year}/{self.month:02d}: {self.percentage}%"
