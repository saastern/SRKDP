from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime
from django.shortcuts import get_object_or_404
from apps.students.models import Class, StudentProfile
from .services import AttendanceCalculator

@api_view(['GET'])
def student_attendance_summary(request, student_id):
    """API: Get student attendance summary with optional date range"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    summary = AttendanceCalculator.get_student_attendance_summary(
        student_id, start_date, end_date
    )
    
    if not summary:
        return Response({'error': 'Student not found'}, status=404)
    
    return Response({
        'student': {
            'id': summary['student'].id,
            'name': summary['student'].user.get_full_name(),
            'roll_number': summary['student'].roll_number,
            'class': summary['student'].student_class.name
        },
        'period': {
            'start_date': summary['start_date'].strftime('%Y-%m-%d'),
            'end_date': summary['end_date'].strftime('%Y-%m-%d')
        },
        'statistics': {
            'total_school_days': summary['total_school_days'],
            'full_present_days': summary['full_present_days'],
            'half_days': summary['half_days'],
            'absent_days': summary['absent_days'],
            'percentage': summary['attendance_percentage']
        },
        'daily_records': [
            {
                'date': record['date'].strftime('%Y-%m-%d'),
                'status': record['status'],
                'morning': record['morning'],
                'afternoon': record['afternoon']
            }
            for record in summary['daily_records'].values()
        ]
    })

@api_view(['GET'])
def class_attendance_today(request, class_id):
    """API: Get today's attendance for entire class"""
    summary = AttendanceCalculator.get_class_attendance_today(class_id)
    
    if not summary:
        return Response({'error': 'Class not found'}, status=404)
    
    return Response({
        'class': {
            'id': summary['class'].id,
            'name': summary['class'].name
        },
        'date': summary['date'].strftime('%Y-%m-%d'),
        'students': [
            {
                'id': item['student'].id,
                'name': item['student'].user.get_full_name(),
                'roll_number': item['student'].roll_number,
                'morning_status': item['morning_status'],
                'afternoon_status': item['afternoon_status'],
                'overall_status': item['overall_status']
            }
            for item in summary['students']
        ]
    })

@api_view(['GET'])
def classes_list(request):
    """API: List all classes with student count"""
    classes = Class.objects.all() # Meta ordering
    return Response({
        'classes': [
            {
                'id': cls.id,
                'name': cls.name,
                'student_count': cls.studentprofile_set.count()
            }
            for cls in classes
        ]
    })
