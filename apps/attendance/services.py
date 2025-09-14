from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import AttendanceRecord, AttendanceSession, AttendanceSummary
from apps.students.models import StudentProfile

class AttendanceCalculator:
    """Service to calculate attendance using your existing models"""
    
    @staticmethod
    def get_student_attendance_summary(student_id, start_date=None, end_date=None):
        """Calculate comprehensive attendance summary for a student"""
        try:
            student = StudentProfile.objects.get(id=student_id)
        except StudentProfile.DoesNotExist:
            return None
        
        # Default date range: current academic year or from first record
        if not start_date:
            first_session = AttendanceSession.objects.filter(
                student_class=student.student_class
            ).order_by('date').first()
            start_date = first_session.date if first_session else timezone.now().date()
        
        if not end_date:
            end_date = timezone.now().date()
        
        # Get all attendance records for this student in the date range
        records = AttendanceRecord.objects.get_student_attendance(
            student, start_date, end_date
        )
        
        # Organize records by date
        daily_attendance = {}
        for record in records:
            date = record.session.date
            date_str = date.strftime('%Y-%m-%d')
            
            if date_str not in daily_attendance:
                daily_attendance[date_str] = {
                    'date': date,
                    'morning': None,
                    'afternoon': None,
                    'status': 'ABSENT'
                }
            
            # Map your existing session values to our status
            session_key = record.session.session  # 'morning' or 'afternoon'
            daily_attendance[date_str][session_key] = record.status
        
        # Calculate statistics
        total_school_days = 0
        full_present_days = 0
        half_days = 0
        absent_days = 0
        
        # Iterate through all school days in range
        current_date = start_date
        while current_date <= end_date:
            # Only count weekdays as school days
            if current_date.weekday() < 5:  # Monday=0 to Friday=4
                total_school_days += 1
                date_str = current_date.strftime('%Y-%m-%d')
                
                if date_str in daily_attendance:
                    morning = daily_attendance[date_str]['morning']
                    afternoon = daily_attendance[date_str]['afternoon']
                    
                    # Determine overall status for the day
                    if morning == 'PRESENT' and afternoon == 'PRESENT':
                        full_present_days += 1
                        daily_attendance[date_str]['status'] = 'FULL_PRESENT'
                    elif morning == 'PRESENT' or afternoon == 'PRESENT':
                        half_days += 1
                        daily_attendance[date_str]['status'] = 'HALF_DAY'
                    else:
                        absent_days += 1
                        daily_attendance[date_str]['status'] = 'ABSENT'
                else:
                    # No records for this date = absent
                    absent_days += 1
                    daily_attendance[date_str] = {
                        'date': current_date,
                        'morning': None,
                        'afternoon': None,
                        'status': 'ABSENT'
                    }
            
            current_date += timedelta(days=1)
        
        # Calculate percentage (full day = 1.0, half day = 0.5)
        total_present_value = full_present_days + (half_days * 0.5)
        percentage = (total_present_value / total_school_days * 100) if total_school_days > 0 else 0
        
        return {
            'student': student,
            'start_date': start_date,
            'end_date': end_date,
            'total_school_days': total_school_days,
            'full_present_days': full_present_days,
            'half_days': half_days,
            'absent_days': absent_days,
            'attendance_percentage': round(percentage, 2),
            'daily_records': daily_attendance
        }
    
    @staticmethod
    def get_class_attendance_today(class_id):
        """Get today's attendance for entire class"""
        from apps.students.models import Class
        
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return None
        
        today = timezone.now().date()
        students = StudentProfile.objects.filter(student_class=class_obj)
        
        # Get today's sessions for this class
        sessions = AttendanceSession.objects.filter(
            student_class=class_obj,
            date=today
        )
        
        summary = []
        for student in students:
            morning_status = None
            afternoon_status = None
            
            # Get student's records for today
            records = AttendanceRecord.objects.filter(
                student=student,
                session__in=sessions
            ).select_related('session')
            
            for record in records:
                if record.session.session == 'morning':
                    morning_status = record.status
                elif record.session.session == 'afternoon':
                    afternoon_status = record.status
            
            # Determine overall status
            if morning_status == 'PRESENT' and afternoon_status == 'PRESENT':
                overall_status = 'FULL_PRESENT'
            elif morning_status == 'PRESENT' or afternoon_status == 'PRESENT':
                overall_status = 'HALF_DAY'
            else:
                overall_status = 'ABSENT'
            
            summary.append({
                'student': student,
                'morning_status': morning_status,
                'afternoon_status': afternoon_status,
                'overall_status': overall_status
            })
        
        return {
            'class': class_obj,
            'date': today,
            'students': summary
        }
    
    @staticmethod
    def compute_monthly_summary(student_id, year, month):
        """Compute and save monthly summary for performance"""
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        summary_data = AttendanceCalculator.get_student_attendance_summary(
            student_id, start_date, end_date
        )
        
        if summary_data:
            summary, created = AttendanceSummary.objects.update_or_create(
                student_id=student_id,
                year=year,
                month=month,
                defaults={
                    'total_school_days': summary_data['total_school_days'],
                    'full_present_days': summary_data['full_present_days'],
                    'half_days': summary_data['half_days'],
                    'absent_days': summary_data['absent_days'],
                    'percentage': summary_data['attendance_percentage']
                }
            )
            return summary
        return None
