from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime
from apps.students.models import StudentProfile, Class
from .models import AttendanceSession, AttendanceRecord

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_class_students(request, class_id):
    """Get all students for a specific class"""
    try:
        students = StudentProfile.objects.filter(student_class_id=class_id).select_related('user', 'student_class')
        
        students_data = []
        for student in students:
            full_name = f"{student.user.first_name} {student.user.last_name}".strip()
            if not full_name:
                full_name = student.user.username
            
            students_data.append({
                'id': student.id,
                'name': full_name,
                'roll_number': student.roll_number,
                'father_name': student.user.first_name,
                'mother_name': student.user.last_name,
                'parent_phone': student.mother_phone,
                'parent_email': student.user.email,
                'address': '',
                'gender': '',
                'father_phone': student.father_phone,
                'mother_phone': student.mother_phone,
            })
        
        return Response({
            'success': True,
            'students': students_data,
            'count': len(students_data)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching students: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# FIXED: Changed from POST to GET and fixed parameter access
@api_view(['GET'])  # ← Changed from POST to GET
@permission_classes([IsAuthenticated])
def get_attendance_report(request):
    """
    Get comprehensive attendance report for all classes for a specific date and session
    """
    try:
        date_str = request.GET.get('date')
        session = request.GET.get('session', 'morning')
        
        if not date_str:
            return Response({
                'success': False,
                'message': 'Date parameter required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get all attendance sessions for the specified date and session
        attendance_sessions = AttendanceSession.objects.filter(
            date=attendance_date,
            session=session
        ).select_related('student_class', 'teacher')
        
        if not attendance_sessions.exists():
            return Response({
                'success': True,
                'data': {
                    'total_classes': 0,
                    'total_students': 0,
                    'total_present': 0,
                    'total_absent': 0,
                    'overall_attendance_rate': 0,
                    'classes': []
                }
            })
        
        # Calculate overall statistics
        total_classes = attendance_sessions.count()
        total_students = 0
        total_present = 0
        total_absent = 0
        classes_data = []
        
        for session_obj in attendance_sessions:
            # Get attendance records for this session
            records = AttendanceRecord.objects.filter(session=session_obj)
            
            class_total_students = records.count()
            class_present_count = records.filter(is_present=True).count()
            class_absent_count = records.filter(is_present=False).count()
            
            # Calculate class attendance rate
            if class_total_students > 0:
                class_attendance_rate = round((class_present_count / class_total_students) * 100, 1)
            else:
                class_attendance_rate = 0
            
            classes_data.append({
                'id': session_obj.student_class.id,
                'name': session_obj.student_class.name,
                'total_students': class_total_students,
                'present_count': class_present_count,
                'absent_count': class_absent_count,
                'attendance_rate': class_attendance_rate,
                'teacher_name': f"{session_obj.teacher.first_name} {session_obj.teacher.last_name}".strip() or session_obj.teacher.username
            })
            
            # Add to overall totals
            total_students += class_total_students
            total_present += class_present_count
            total_absent += class_absent_count
        
        # Calculate overall attendance rate
        overall_attendance_rate = round((total_present / total_students) * 100, 1) if total_students > 0 else 0
        
        return Response({
            'success': True,
            'data': {
                'date': date_str,
                'session': session,
                'total_classes': total_classes,
                'total_students': total_students,
                'total_present': total_present,
                'total_absent': total_absent,
                'overall_attendance_rate': overall_attendance_rate,
                'classes': classes_data
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error generating report: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# FIXED: Added missing decorator
@api_view(['POST'])  # ← Added missing decorator
@permission_classes([IsAuthenticated])
def mark_attendance(request):
    """Save attendance data to database"""
    try:
        data = request.data
        class_id = data.get('class_id')
        session = data.get('session', 'morning')  # morning or afternoon
        date_str = data.get('date')  # YYYY-MM-DD format
        attendance_data = data.get('attendance', [])
        
        if not all([class_id, session, date_str, attendance_data]):
            return Response({
                'success': False,
                'message': 'Missing required fields: class_id, session, date, attendance'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse date
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get or create attendance session
        try:
            student_class = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Class not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        attendance_session, created = AttendanceSession.objects.get_or_create(
            date=attendance_date,
            session=session,
            student_class=student_class,
            defaults={'teacher': request.user}
        )
        
        if not created:
            # Update existing session
            attendance_session.teacher = request.user
            attendance_session.updated_at = timezone.now()
            attendance_session.save()
        
        # Clear existing records for this session (in case of updates)
        AttendanceRecord.objects.filter(session=attendance_session).delete()
        
        # Create new attendance records
        attendance_records = []
        for record in attendance_data:
            student_id = record.get('student_id')
            is_present = record.get('is_present', True)
            
            try:
                student = StudentProfile.objects.get(id=student_id)
                attendance_records.append(AttendanceRecord(
                    session=attendance_session,
                    student=student,
                    is_present=is_present
                ))
            except StudentProfile.DoesNotExist:
                continue
        
        # Bulk create records
        AttendanceRecord.objects.bulk_create(attendance_records)
        
        return Response({
            'success': True,
            'message': f'Attendance saved successfully for {len(attendance_records)} students',
            'session_id': attendance_session.id
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error saving attendance: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attendance(request, class_id):
    """Get existing attendance for a specific class and date"""
    try:
        date_str = request.GET.get('date')
        session = request.GET.get('session', 'morning')
        
        if not date_str:
            return Response({
                'success': False,
                'message': 'Date parameter required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        try:
            attendance_session = AttendanceSession.objects.get(
                date=attendance_date,
                session=session,
                student_class_id=class_id
            )
            
            records = AttendanceRecord.objects.filter(session=attendance_session).select_related('student__user')
            
            attendance_data = {}
            for record in records:
                attendance_data[record.student.id] = record.is_present
            
            return Response({
                'success': True,
                'attendance': attendance_data,
                'session_id': attendance_session.id
            })
            
        except AttendanceSession.DoesNotExist:
            return Response({
                'success': True,
                'attendance': {},
                'message': 'No attendance found for this date/session'
            })
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching attendance: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
