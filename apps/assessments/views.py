from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import *
from django.db.models import Sum, Avg, Count, Q
from .serializers import *
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
            class_group = selected_class.class_group
            max_marks = selected_exam.get_max_marks(class_group)
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
                        'is_main': s.is_main_subject,
                        'max_marks': selected_exam.get_max_marks(class_group, s.subject)
                    } for s in subjects
                ],
                'existing_marks': existing_marks,
                'max_marks': selected_exam.get_max_marks(class_group)
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
                class_group = student.student_class.class_group
                
                for subject_id, mark_data in subjects_marks.items():
                    subject = Subject.objects.get(id=subject_id)
                    
                    max_marks = exam.get_max_marks(class_group, subject)
                    # Update or create mark
                    student_mark, created = StudentMark.objects.update_or_create(
                        student=student,
                        subject=subject,
                        exam=exam,
                        academic_year=academic_year,
                        defaults={
                            'marks_obtained': mark_data['marks'],
                            'max_marks': max_marks,
                            'is_absent': mark_data.get('is_absent', False)
                        }
                    )
            
            return JsonResponse({'success': True, 'message': 'Marks saved successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


# ✅ UPDATED: Database-driven class listing
class ClassListAPIView(APIView):
    """GET /api/assessments/classes/ - List all classes with student counts"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        classes = Class.objects.all().order_by('name')
        
        classes_data = []
        for cls in classes:
            classes_data.append({
                'id': str(cls.id),           # ✅ Use database ID (always unique)
                'name': cls.name,            # ✅ Use actual class name
                'displayName': cls.name,     # ✅ Display actual name
                'studentCount': cls.studentprofile_set.count()
            })
        
        return Response({'classes': classes_data})


# ✅ UPDATED: Database-driven student listing
class StudentListAPIView(APIView):
    """GET /api/assessments/students/?class_id=X - Get students by class"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        class_id = request.query_params.get('class_id')
        if not class_id:
            return Response({'error': 'Class ID is required'}, status=400)
        
        try:
            # ✅ Use database ID directly (no mapping needed)
            selected_class = Class.objects.get(id=class_id)
            
            students = StudentProfile.objects.filter(
                student_class=selected_class
            ).order_by('roll_number')
            
            # Format students data
            students_data = []
            for student in students:
                students_data.append({
                    'id': str(student.id),       # ✅ Use student's actual database ID
                    'rollNo': str(student.roll_number),
                    'name': student.user.get_full_name() or f"Student {student.roll_number}",
                    'className': selected_class.name
                })
            
            return Response({
                'students': students_data,
                'className': selected_class.name
            })
            
        except Class.DoesNotExist:
            return Response({'error': 'Class not found'}, status=404)


# ✅ UPDATED: Database-driven student marks
class StudentMarksDetailAPIView(APIView):
    """GET /api/assessments/student-marks/{student_id}/ - Get REAL student marks"""
    permission_classes = [AllowAny]
    
    def get(self, request, student_id):
        try:
            # ✅ Use student ID directly (no complex parsing needed)
            student = StudentProfile.objects.get(id=student_id)
            
            academic_year = AcademicYear.objects.filter(is_current=True).first()
            if not academic_year:
                return Response({'error': 'No active academic year found'}, status=400)

            response_data = {
                'student': {
                    'id': str(student.id),
                    'name': student.user.get_full_name() or f"Student {student.roll_number}",
                    'rollNo': str(student.roll_number).zfill(2) if isinstance(student.roll_number, int) or str(student.roll_number).isdigit() else str(student.roll_number),
                    'className': student.student_class.name
                },
                'subjects': self.get_subjects_data(student, academic_year),
                'termSummaries': self.get_term_summaries(student, academic_year),
                'classConfig': self.get_class_config(student.student_class)
            }

            return Response(response_data)

        except StudentProfile.DoesNotExist:
            return Response({'error': 'Student not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    def get_subjects_data(self, student, academic_year):
        """Get REAL subject marks data from database"""
        # Get all marks for this student
        marks_queryset = StudentMark.objects.filter(
            student=student,
            academic_year=academic_year
        ).select_related('subject', 'exam')
        
        # Get all subjects for this class
        class_subjects = ClassSubjectMapping.objects.filter(
            student_class=student.student_class,
            academic_year=academic_year
        ).select_related('subject')
        
        subjects_data = []
        
        for class_subject in class_subjects:
            subject = class_subject.subject
            subject_data = {
                'name': subject.name,
                'fa1': {'marks': 0, 'grade': 'N/A', 'maxMarks': 0},
                'fa2': {'marks': 0, 'grade': 'N/A', 'maxMarks': 0},
                'fa3': {'marks': 0, 'grade': 'N/A', 'maxMarks': 0},
                'fa4': {'marks': 0, 'grade': 'N/A', 'maxMarks': 0},
                'sa1': {'marks': 0, 'grade': 'N/A', 'maxMarks': 0},
                'sa2': {'marks': 0, 'grade': 'N/A', 'maxMarks': 0},
            }
            
            # Fill with REAL marks data
            subject_marks = marks_queryset.filter(subject=subject)
            for mark in subject_marks:
                exam_key = mark.exam.name.lower()
                if exam_key in subject_data:
                    subject_data[exam_key] = {
                        'marks': float(mark.marks_obtained),
                        'grade': mark.grade,
                        'maxMarks': mark.max_marks
                    }
            
            subjects_data.append(subject_data)
        
        return subjects_data
    
    def get_term_summaries(self, student, academic_year):
        """Calculate REAL term summaries from database"""
        summaries = []
        
        for exam_name in ['FA1', 'FA2', 'FA3', 'FA4', 'SA1', 'SA2']:
            try:
                exam = Exam.objects.get(name=exam_name)
                
                # Get marks for this exam
                exam_marks = StudentMark.objects.filter(
                    student=student,
                    exam=exam,
                    academic_year=academic_year
                )
                
                if exam_marks.exists():
                    total_marks = sum(float(m.marks_obtained) for m in exam_marks)
                    max_marks = sum(m.max_marks for m in exam_marks)
                    percentage = (total_marks / max_marks * 100) if max_marks > 0 else 0
                    
                    # Calculate grade
                    grade = self.calculate_overall_grade(percentage)
                    
                    # Calculate class rank (simplified - you can enhance this)
                    class_rank = self.calculate_class_rank(student, exam, academic_year)
                    
                    summaries.append({
                        'term': exam_name.replace('FA', 'FA-').replace('SA', 'SA-'),
                        'totalMarks': int(total_marks),
                        'maxMarks': max_marks,
                        'percentage': round(percentage, 2),
                        'grade': grade,
                        'classRank': class_rank,
                        'totalStudents': student.student_class.studentprofile_set.count()
                    })
                
            except Exam.DoesNotExist:
                continue
        
        return summaries
    
    def calculate_overall_grade(self, percentage):
        """Calculate overall grade from percentage"""
        if percentage >= 90: return 'A+'
        elif percentage >= 80: return 'A'
        elif percentage >= 70: return 'B+'
        elif percentage >= 60: return 'B'
        elif percentage >= 50: return 'C+'
        elif percentage >= 40: return 'C'
        elif percentage >= 33: return 'D'
        else: return 'F'
    
    def calculate_class_rank(self, student, exam, academic_year):
        """Calculate student's rank in class for this exam"""
        # This is a simplified ranking - you can enhance it
        # Get all students' totals for this exam in this class
        class_students = StudentProfile.objects.filter(student_class=student.student_class)
        
        student_totals = []
        for cls_student in class_students:
            cls_marks = StudentMark.objects.filter(
                student=cls_student,
                exam=exam,
                academic_year=academic_year
            )
            if cls_marks.exists():
                total = sum(float(m.marks_obtained) for m in cls_marks)
                student_totals.append((cls_student.id, total))
        
        # Sort by total marks (highest first)
        student_totals.sort(key=lambda x: x[1], reverse=True)
        
        # Find rank
        for rank, (student_id, total) in enumerate(student_totals, 1):
            if student_id == student.id:
                return rank
        
        return 1  # Default rank
    
    def get_class_config(self, student_class):
        """Get class configuration based on class group"""
        class_group = student_class.class_group
        
        # Map to frontend class config format
        if class_group == 'pre':
            return {
                'faMarks': 50,
                'saMarks': 100,
                'excludeFromTotal': ['Color'],
                'gradingScale': 'lower'
            }
        elif class_group in ['1-2', '1-5', '3-5']:
            return {
                'faMarks': 25,
                'saMarks': 100,
                'excludeFromTotal': ['GK', 'Computer'],
                'gradingScale': 'lower'
            }
        else:  # 6-10
            return {
                'faMarks': 50,
                'saMarks': 100,
                'excludeFromTotal': ['GK', 'Computer'],
                'gradingScale': 'higher'
            }


@api_view(['POST'])
@permission_classes([AllowAny])
def teacher_login_api(request):
    """POST /api/assessments/auth/login/ - Teacher authentication"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({'error': 'Email and password required'}, status=400)
    
    # TODO: Implement real authentication with your User model
    # For now, returning success for any valid email/password
    if email and password:
        return Response({
            'teacher': {
                'id': '1',
                'name': 'Teacher Name',  # Get from your User model
                'email': email
            }
        })
    
    return Response({'error': 'Invalid credentials'}, status=401)