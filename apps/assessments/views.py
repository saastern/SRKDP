from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import *
from apps.students.models import Class, StudentProfile

@login_required
def marks_entry_sheet(request):
    """Excel-like marks entry interface"""
    classes = Class.objects.all().order_by('name')
    exams = Exam.objects.all().order_by('order')
    academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    context = {
        'classes': classes,
        'exams': exams,
        'academic_year': academic_year,
    }
    return render(request, 'assessments/marks_entry_sheet.html', context)

@csrf_exempt
def get_marks_sheet_data(request):
    """Get students and subjects for selected class and exam"""
    if request.method == 'POST':
        data = json.loads(request.body)
        class_id = data.get('class_id')
        exam_id = data.get('exam_id')
        
        try:
            academic_year = AcademicYear.objects.filter(is_current=True).first()
            selected_class = Class.objects.get(id=class_id)
            selected_exam = Exam.objects.get(id=exam_id)
            
            # Get students in this class
            students = StudentProfile.objects.filter(
                student_class=selected_class
            ).order_by('roll_number')
            
            # Get subjects for this class
            subjects = ClassSubjectMapping.objects.filter(
                student_class=selected_class,
                academic_year=academic_year
            ).select_related('subject').order_by('is_main_subject', 'subject__name')
            
            # Get existing marks
            existing_marks = {}
            for student in students:
                student_marks = StudentMark.objects.filter(
                    student=student,
                    exam=selected_exam,
                    academic_year=academic_year
                ).select_related('subject')
                
                existing_marks[student.id] = {}
                for mark in student_marks:
                    existing_marks[student.id][mark.subject.id] = {
                        'marks': float(mark.marks_obtained),
                        'grade': mark.grade,
                        'is_absent': mark.is_absent
                    }
            
            return JsonResponse({
                'success': True,
                'students': [
                    {
                        'id': s.id,
                        'name': s.user.get_full_name() or s.user.username,
                        'roll_number': s.roll_number
                    } for s in students
                ],
                'subjects': [
                    {
                        'id': s.subject.id,
                        'name': s.subject.name,
                        'is_main': s.is_main_subject
                    } for s in subjects
                ],
                'existing_marks': existing_marks,
                'max_marks': 50
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt 
def save_marks_sheet(request):
    """Save marks from the spreadsheet"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        try:
            academic_year = AcademicYear.objects.filter(is_current=True).first()
            exam = Exam.objects.get(id=data['exam_id'])
            
            for student_id, subjects_marks in data['marks'].items():
                student = StudentProfile.objects.get(id=student_id)
                
                for subject_id, mark_data in subjects_marks.items():
                    subject = Subject.objects.get(id=subject_id)
                    
                    # Update or create mark
                    student_mark, created = StudentMark.objects.update_or_create(
                        student=student,
                        subject=subject,
                        exam=exam,
                        academic_year=academic_year,
                        defaults={
                            'marks_obtained': mark_data['marks'],
                            'max_marks': exam.max_marks,
                            'is_absent': mark_data.get('is_absent', False)
                        }
                    )
            
            return JsonResponse({'success': True, 'message': 'Marks saved successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
