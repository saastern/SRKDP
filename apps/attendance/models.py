from django.db import models
from django.utils import timezone
from apps.students.models import StudentProfile

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
    
    class Meta:
        unique_together = ['session', 'student']
    
    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student.user.first_name} {self.student.user.last_name} - {status}"
