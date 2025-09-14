from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from datetime import datetime
from .models import *
from .services import GradingService
from apps.students.models import Class

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_marks_entry_form_data(request):
    """Get all data needed for marks entry form in one API call"""
    try:
        class_id = request.GET.get('class_id')
        exam_id = request.GET.get('exam_id')
        subject_id = request.GET.get('subject_id')
        
        if not class_id or not exam_id:
            return Response({
                'success': False,
                'message': 'class_id and exam_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get current academic year
        academic_year = AcademicYear.objects.filter(is_current=True).first()
        if not academic_year:
            return Response({
                'success': False,
                'message': 'No current academic year found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get class and exam info
        class_obj = get_object_or_404(Class, id=class_id)
        exam = get_object_or_404(Exam, id=exam_id)
        
        # Get students in this class
        students = StudentProfile.objects.filter(
            student_class=class_obj
        ).select_related('user').order_by('roll_number')
        
        # Get subjects for this class
        subject_mappings = ClassSubjectMapping.objects.filter(
            student_class=class_obj,
            academic_year=academic_year
        ).select_related('subject')
        
        if subject_id:
            subject_mappings = subject_mappings.filter(subject_id=subject_id)
        
        subjects = [mapping.subject for mapping in subject_mappings]
        
        # Get existing marks
        existing_marks = {}
        if subjects:
            marks_qs = StudentMark.objects.filter(
                student__student_class=class_obj,
                exam=exam,
                subject__in=subjects,
                academic_year=academic_year
            )
            
            for mark in marks_qs:
                student_id = str(mark.student.id)
                subject_id_str = str(mark.subject.id)
                
                if student_id not in existing_marks:
                    existing_marks[student_id] = {}
                existing_marks[student_id][subject_id_str] = {
                    'marks': float(mark.marks_obtained),
                    'grade': mark.grade,
                    'is_absent': mark.is_absent
                }
        
        return Response({
            'success': True,
            'form_data': {
                'class': {
                    'id': class_obj.id,
                    'name': class_obj.name,
                    'class_group': class_obj.class_group
                },
                'exam': {
                    'id': exam.id,
                    'name': exam.name,
                    'max_marks': exam.get_max_marks(class_obj.class_group)
                },
                'subjects': [
                    {
                        'id': subj.id,
                        'name': subj.name,
                        'is_main': next((m.is_main_subject for m in subject_mappings if m.subject == subj), True)
                    }
                    for subj in subjects
                ],
                'students': [
                    {
                        'id': student.id,
                        'name': student.user.get_full_name(),
                        'roll_number': student.roll_number
                    }
                    for student in students
                ],
                'existing_marks': existing_marks,
                'academic_year_id': academic_year.id
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enter_marks(request):
    """Enter marks for students"""
    try:
        data = request.data
        subject_id = data.get('subject_id')
        exam_id = data.get('exam_id')
        academic_year_id = data.get('academic_year_id')
        marks_data = data.get('marks', [])
        
        # Get objects
        subject = get_object_or_404(Subject, id=subject_id)
        exam = get_object_or_404(Exam, id=exam_id)
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        
        saved_count = 0
        
        for mark_entry in marks_data:
            student_id = mark_entry.get('student_id')
            marks = mark_entry.get('marks', 0)
            is_absent = mark_entry.get('is_absent', False)
            
            student = get_object_or_404(StudentProfile, id=student_id)
            max_marks = exam.get_max_marks(student.student_class.class_group)
            
            # Create or update marks
            student_mark, created = StudentMark.objects.update_or_create(
                student=student,
                subject=subject,
                exam=exam,
                academic_year=academic_year,
                defaults={
                    'marks_obtained': marks if not is_absent else 0,
                    'max_marks': max_marks,
                    'is_absent': is_absent,
                    'entered_by': request.user
                }
            )
            saved_count += 1
            
            # Calculate summary
            GradingService.calculate_student_exam_summary(
                student_id, exam_id, academic_year_id
            )
        
        return Response({
            'success': True,
            'message': f'Marks saved for {saved_count} students'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_classes_and_exams(request):
    """Get classes and exams for dropdowns"""
    classes = Class.objects.all().order_by('name')
    exams = Exam.objects.filter(is_active=True).order_by('exam_type', 'order')
    
    return Response({
        'success': True,
        'data': {
            'classes': [
                {'id': cls.id, 'name': cls.name, 'class_group': cls.class_group}
                for cls in classes
            ],
            'exams': [
                {'id': exam.id, 'name': exam.name, 'exam_type': exam.exam_type}
                for exam in exams
            ]
        }
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_marks(request, student_id, exam_id):
    """Get all marks for a student with overall grade and class rank"""
    try:
        academic_year = AcademicYear.objects.filter(is_current=True).first()
        student = StudentProfile.objects.get(id=student_id)
        
        # Get student's marks
        marks = StudentMark.objects.filter(
            student_id=student_id,
            exam_id=exam_id,
            academic_year=academic_year
        ).select_related('subject')
        
        total_marks = 0
        max_marks = 0
        marks_data = []
        
        for mark in marks:
            marks_data.append({
                'subject': mark.subject.name,
                'marks_obtained': float(mark.marks_obtained),
                'max_marks': mark.max_marks,
                'grade': mark.grade,
                'grade_point': float(mark.grade_point),
                'is_absent': mark.is_absent
            })
            total_marks += mark.marks_obtained
            max_marks += mark.max_marks
        
        percentage = (total_marks / max_marks * 100) if max_marks > 0 else 0
        
        # Calculate overall grade based on percentage
        def calculate_overall_grade(percentage):
            if percentage >= 91: return "A1", 10.0
            elif percentage >= 81: return "A2", 9.0
            elif percentage >= 71: return "B1", 8.0
            elif percentage >= 61: return "B2", 7.0
            elif percentage >= 51: return "C1", 6.0
            elif percentage >= 41: return "C2", 5.0
            elif percentage >= 33: return "D", 4.0
            else: return "E", 0.0
        
        overall_grade, overall_gpa = calculate_overall_grade(percentage)
        
        # Calculate class rank
        from django.db.models import Sum, F
        class_students = StudentProfile.objects.filter(
            student_class=student.student_class
        ).values('id')
        
        # Get total marks for all students in the same class and exam
        student_totals = []
        for class_student in class_students:
            student_marks_sum = StudentMark.objects.filter(
                student_id=class_student['id'],
                exam_id=exam_id,
                academic_year=academic_year
            ).aggregate(total=Sum('marks_obtained'))['total'] or 0
            
            student_totals.append({
                'student_id': class_student['id'],
                'total_marks': student_marks_sum
            })
        
        # Sort by total marks (descending) to get ranks
        student_totals.sort(key=lambda x: x['total_marks'], reverse=True)
        
        # Find current student's rank
        current_rank = 1
        for i, student_total in enumerate(student_totals, 1):
            if student_total['student_id'] == student_id:
                current_rank = i
                break
        
        return Response({
            'success': True,
            'student_id': student_id,
            'student_name': student.user.get_full_name() or student.user.username,
            'class_name': student.student_class.name,
            'exam_id': exam_id,
            'marks': marks_data,
            'summary': {
                'total_marks_obtained': float(total_marks),
                'total_max_marks': max_marks,
                'percentage': round(percentage, 2),
                'overall_grade': overall_grade,
                'overall_gpa': overall_gpa,
                'class_rank': current_rank,
                'total_students_in_class': len(student_totals),
                'total_subjects': len(marks_data)
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)
