from django.db import models
from apps.users.models import User

class Class(models.Model):
    name = models.CharField(max_length=30)
    class_group  = models.CharField(max_length=10, choices=[('pre','Pre-Primary'),('1-5','Primary'),('6-10','Secondary')]) # E.g. "A", "B", etc.
    def __str__(self): return self.name

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True)
    roll_number = models.CharField(max_length=10)
    mother_phone = models.CharField(max_length=15)
    father_phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.student_class})"
