from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AttendanceSession, AttendanceRecord

class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    readonly_fields = ['student_info', 'marked_at']
    fields = ['student_info', 'is_present', 'marked_at']
    
    def student_info(self, obj):
        if obj.student:
            return f"{obj.student.user.first_name} {obj.student.user.last_name} (Roll: {obj.student.roll_number})"
        return "-"
    student_info.short_description = "Student"

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['student_class', 'date', 'session', 'teacher', 'total_students', 'present_count', 'absent_count', 'attendance_percentage']
    list_filter = ['date', 'session', 'student_class', 'teacher']
    search_fields = ['student_class__name', 'teacher__username']
    date_hierarchy = 'date'
    inlines = [AttendanceRecordInline]
    
    def total_students(self, obj):
        return obj.records.count()
    total_students.short_description = "Total Students"
    
    def present_count(self, obj):
        count = obj.records.filter(is_present=True).count()
        return format_html('<span style="color: green; font-weight: bold;">{}</span>', count)
    present_count.short_description = "Present"
    
    def absent_count(self, obj):
        count = obj.records.filter(is_present=False).count()
        if count > 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', count)
        return count
    absent_count.short_description = "Absent"
    
    def attendance_percentage(self, obj):
        total = obj.records.count()
        if total == 0:
            return "0%"
        present = obj.records.filter(is_present=True).count()
        percentage = (present / total) * 100
        color = "green" if percentage >= 80 else "orange" if percentage >= 60 else "red"
        return format_html('<span style="color: {}; font-weight: bold;">{:.1f}%</span>', color, percentage)
    attendance_percentage.short_description = "Attendance %"

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'student_roll', 'student_class', 'session_date', 'session_type', 'is_present', 'marked_at']
    list_filter = ['is_present', 'session__date', 'session__session', 'session__student_class']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__roll_number']
    date_hierarchy = 'session__date'
    
    def student_name(self, obj):
        return f"{obj.student.user.first_name} {obj.student.user.last_name}"
    student_name.short_description = "Student Name"
    
    def student_roll(self, obj):
        return obj.student.roll_number
    student_roll.short_description = "Roll Number"
    
    def student_class(self, obj):
        return obj.session.student_class.name
    student_class.short_description = "Class"
    
    def session_date(self, obj):
        return obj.session.date
    session_date.short_description = "Date"
    
    def session_type(self, obj):
        return obj.session.get_session_display()
    session_type.short_description = "Session"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student__user', 'student__student_class', 'session__student_class'
        )
