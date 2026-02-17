# apps/notifications/models.py
from django.db import models
from django.conf import settings

class Announcement(models.Model):
    TARGET_CHOICES = [
        ('all', 'All Staff'),
        ('teachers', 'Teachers Only'),
        ('students', 'Students Only'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='announcements'
    )
    target_role = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return self.title
