# apps/notifications/urls.py
from django.urls import path
from .views import announcements_list_create, delete_announcement

app_name = 'notifications'
urlpatterns = [
    path('announcements/', announcements_list_create, name='announcements'),
    path('announcements/<int:announcement_id>/delete/', delete_announcement, name='delete_announcement'),
]
