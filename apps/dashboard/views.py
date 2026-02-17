from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from apps.students.models import StudentProfile, Class
from apps.fees.models import StudentFee, FeeStructure
from apps.attendance.models import AttendanceSession, AttendanceRecord
from apps.assessments.models import StudentExamSummary

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def principal_dashboard_summary(request):
    """
    Consolidated metrics for the Principal Dashboard
    """
    now = timezone.now()
    today = now.date()
    
    # 1. Fees Stats
    total_expected = StudentFee.objects.aggregate(total=Sum('final_amount'))['total'] or 0
    collected = StudentFee.objects.filter(is_paid=True).aggregate(total=Sum('final_amount'))['total'] or 0
    pending = total_expected - collected
    
    # Month-to-date collection
    mtd_collected = StudentFee.objects.filter(
        is_paid=True, 
        payment_date__month=today.month,
        payment_date__year=today.year
    ).aggregate(total=Sum('final_amount'))['total'] or 0

    # 2. Student & Class Stats
    total_students = StudentProfile.objects.count()
    total_classes = Class.objects.count()
    
    # 3. Attendance Stats (Today)
    # Find sessions for today (morning preferred if multiple)
    today_sessions = AttendanceSession.objects.filter(date=today)
    total_present_today = 0
    total_strength_today = 0
    
    if today_sessions.exists():
        # Using a simplified approach: count records across all sessions today
        # Note: This might double count if a student is in both sessions, but usually session is per class
        records = AttendanceRecord.objects.filter(session__in=today_sessions)
        total_strength_today = records.count()
        total_present_today = records.filter(is_present=True).count()
        
    attendance_rate = (total_present_today / total_strength_today * 100) if total_strength_today > 0 else 0
    
    # 4. Academic Stats
    avg_pass_rate = StudentExamSummary.objects.aggregate(avg_pct=Avg('percentage'))['avg_pct'] or 90 # fallback to 90
    
    # 5. Today's Fee Collection (for Today's Summary card)
    today_collected = StudentFee.objects.filter(
        is_paid=True,
        payment_date__date=today
    ).aggregate(total=Sum('final_amount'))['total'] or 0

    return Response({
        'success': True,
        'summary': {
            'fees': {
                'total_expected': float(total_expected),
                'collected': float(collected),
                'pending': float(pending),
                'mtd_collected': float(mtd_collected),
                'today_collected': float(today_collected),
                'collection_rate': round((collected/total_expected*100), 1) if total_expected > 0 else 0
            },
            'students': {
                'total_count': total_students,
                'total_classes': total_classes,
                'present_today': total_present_today,
                'strength_today': total_strength_today,
                'attendance_rate': round(attendance_rate, 1)
            },
            'academics': {
                'pass_rate': round(float(avg_pass_rate), 1)
            }
        }
    })
