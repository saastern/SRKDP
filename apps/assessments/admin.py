from django.contrib import admin
from .models import *

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current', 'is_active']
    list_filter = ['is_current', 'is_active']
    list_editable = ['is_active']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    search_fields = ['name', 'code']
    list_filter = ['is_active']

@admin.register(ClassSubjectMapping)
class ClassSubjectMappingAdmin(admin.ModelAdmin):
    list_display = ['student_class', 'subject', 'is_main_subject', 'academic_year']
    list_filter = ['is_main_subject', 'academic_year', 'student_class']
    search_fields = ['subject__name', 'student_class__name']

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['name', 'exam_type', 'order', 'is_active']
    list_filter = ['exam_type', 'is_active']
    ordering = ['exam_type', 'order']

@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = ['class_group', 'exam_type', 'min_marks', 'max_marks', 'grade', 'grade_point']
    list_filter = ['class_group', 'exam_type']
    ordering = ['class_group', 'exam_type', '-min_marks']

@admin.register(StudentMark)
class StudentMarkAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'exam', 'marks_obtained', 'max_marks', 'grade', 'grade_point']
    list_filter = ['exam', 'subject', 'academic_year', 'grade']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'subject__name']
    readonly_fields = ['grade', 'grade_point', 'entered_at', 'updated_at']

@admin.register(StudentExamSummary)
class StudentExamSummaryAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'percentage', 'overall_grade', 'class_rank']
    list_filter = ['exam', 'academic_year']
    search_fields = ['student__user__first_name', 'student__user__last_name']
