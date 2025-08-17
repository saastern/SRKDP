from django.db import models
from apps.users.models import User

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subjects = models.CharField(max_length=100)  # E.g. "Math,Science"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
