from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta
from calendar import month_abbr
from .models import StudentFee, FeeStructure
from apps.students.models import StudentProfile

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def principal_fee_dashboard(request):
    now = timezone.now()
    
    # KPI Data
    total_expected = FeeStructure.objects.aggregate(total=Sum('amount'))['total'] or 0
    collected = StudentFee.objects.filter(is_paid=True).aggregate(total=Sum('final_amount'))['total'] or 0
    pending = StudentFee.objects.filter(is_paid=False, final_amount__gt=0).aggregate(total=Sum('final_amount'))['total'] or 0
    concessions = StudentFee.objects.filter(concession_amount__gt=0).aggregate(total=Sum('concession_amount'))['total'] or 0
    defaulters = StudentFee.objects.filter(is_paid=False, final_amount__gt=0).values('student').distinct().count()
    
    # Monthly Chart Data (Last 6 months)
    chart_data = []
    for i in range(6):
        month_ago = now - timedelta(days=30*i)
        month_collected = StudentFee.objects.filter(
            payment_date__month=month_ago.month,
            payment_date__year=month_ago.year,
            is_paid=True
        ).aggregate(total=Sum('final_amount'))['total'] or 0
        
        chart_data.append({
            'month': month_abbr[month_ago.month],
            'amount': float(month_collected)
        })
    
    # Recent Transactions
    recent = StudentFee.objects.filter(is_paid=True).select_related('student__user')[:10]
    
    return Response({
        'kpis': {
            'total_expected': float(total_expected),
            'collected': float(collected),
            'pending': float(pending),
            'concessions': float(concessions),
            'defaulters_count': defaulters,
            'collection_rate': round((collected/total_expected*100), 1) if total_expected else 0
        },
        'charts': {'monthly_collections': chart_data},
        'recent_transactions': [{
            'student': f"{fee.student.user.get_full_name()} ({fee.student.roll_number})",
            'amount': float(fee.final_amount),
            'concession': float(fee.concession_amount),
            'date': fee.payment_date.strftime('%Y-%m-%d %H:%M') if fee.payment_date else '',
            'receipt': fee.receipt_number
        } for fee in recent]
    })
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_payment(request):
    data = request.data
    student_id = data.get('student_id')
    amount_paid = data.get('amount_paid')
    concession = data.get('concession', 0)
    payment_method = data.get('payment_method', 'CASH')
    receipt_no = data.get('receipt_no')
    notes = data.get('notes', '')

    try:
        student = StudentProfile.objects.get(id=student_id)
        # Find or create a fee structure for this student's class group and current month
        now = timezone.now()
        month_str = now.strftime('%b-%Y') # e.g. "Jan-2026"
        
        # Determine class group (this is a bit simplified, usually mapping class to group)
        class_group = student.student_class.class_group if student.student_class else '1-10'
        
        structure, _ = FeeStructure.objects.get_or_create(
            class_group=class_group,
            fee_month=month_str,
            defaults={'amount': amount_paid + concession, 'due_date': now.date()}
        )
        
        fee_record = StudentFee.objects.create(
            student=student,
            fee_structure=structure,
            amount_due=amount_paid + concession,
            concession_amount=concession,
            is_paid=True,
            payment_date=now,
            payment_method=payment_method,
            receipt_number=receipt_no,
            notes=notes
        )
        
        return Response({
            'success': True, 
            'message': 'Payment recorded successfully',
            'payment': {
                'id': fee_record.id,
                'receipt_no': fee_record.receipt_number,
                'amount': float(fee_record.final_amount)
            }
        })
    except StudentProfile.DoesNotExist:
        return Response({'success': False, 'message': 'Student not found'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)
