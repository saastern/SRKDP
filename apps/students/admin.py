from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import StudentProfile, Class

# Keep your existing StudentProfileInline
class StudentProfileInline(admin.TabularInline):
    model = StudentProfile
    extra = 0
    readonly_fields = ('user', 'roll_number', 'mother_phone', 'father_phone')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

# REPLACE your current ClassAdmin with this enhanced version:
@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_count', 'view_students_link')
    inlines = [StudentProfileInline]
    
    def student_count(self, obj):
        return obj.studentprofile_set.count()
    student_count.short_description = 'Number of Students'
    
    def view_students_link(self, obj):
        count = obj.studentprofile_set.count()
        if count > 0:
            url = reverse("admin:students_studentprofile_changelist") + f"?student_class__id={obj.id}"
            return format_html('<a href="{}">View {} Students</a>', url, count)
        return "No students"
    view_students_link.short_description = 'Students'

# Keep your existing StudentProfileAdmin as is
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_class', 'roll_number', 'mother_phone', 'father_phone')
    search_fields = ('user__first_name', 'user__last_name', 'roll_number')
    list_filter = ('student_class',)
