from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta
from decimal import Decimal
from calendar import month_abbr
from .models import StudentFee, FeeStructure, FeeTransaction
from apps.students.models import StudentProfile, Class

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
    
    # Recent Transactions - use .only() to skip missing columns
    recent = StudentFee.objects.filter(is_paid=True).select_related('student__user').only(
        'id', 'student', 'is_paid', 'final_amount', 'payment_date', 
        'receipt_number', 'amount_due', 'concession_amount'
    )[:10]
    
    # Robust transaction mapping
    def get_fee_amount(fee):
        # Fallback to amount_due or final_amount if other fields fail
        return getattr(fee, 'total_amount', getattr(fee, 'final_amount', fee.amount_due))

    return Response({
        'kpis': {
            'total_expected': float(total_expected),
            'collected': float(collected),
            'pending': float(pending),
            'concessions': float(concessions),
            'defaulters_count': defaulters,
            'collection_rate': round(float(collected/total_expected*100), 1) if total_expected else 0
        },
        'charts': {'monthly_collections': chart_data},
        'recent_transactions': [{
            'student': f"{fee.student.user.get_full_name()} ({fee.student.roll_number})",
            'amount': float(get_fee_amount(fee)),
            'concession': float(fee.concession_amount),
            'date': fee.payment_date.strftime('%Y-%m-%d %H:%M') if fee.payment_date else '',
            'receipt': fee.receipt_number
        } for fee in recent]
    })
@api_view(['GET'])
@permission_classes([AllowAny])
def get_student_fee_status(request):
    print(f"DEBUG: get_student_fee_status hit with student_id={request.query_params.get('student_id')}")
    student_id = request.query_params.get('student_id')
    if not student_id:
        return Response({'error': 'Student ID required'}, status=400)
    
    try:
        student = StudentProfile.objects.get(id=student_id)
        now = timezone.now()
        month_str = now.strftime('%b-%Y')
        
        # Check for existing fee record for current month - use .only() to skip missing columns
        fee_record = StudentFee.objects.filter(
            student=student, 
            fee_structure__fee_month=month_str
        ).only(
            'id', 'student', 'fee_structure', 'amount_due', 
            'concession_amount', 'final_amount', 'is_paid', 
            'payment_date', 'payment_method', 'receipt_number', 
            'notes', 'created_at'
        ).first()
        
        if not fee_record:
            return Response({
                'exists': False,
                'student': {
                    'name': student.user.get_full_name(),
                    'class': student.student_class.name if student.student_class else 'N/A'
                },
                'fee_id': None,
                'total_assigned': 0.0,
                'concession': 0.0,
                'final_total': 0.0,
                'balance': 0.0,
                'is_paid': False,
                'history': []
            })
            
        # Get transaction history
        transactions = []
        try:
            transactions = FeeTransaction.objects.filter(student_fee=fee_record).order_by('-payment_date')
        except Exception:
            pass # In case table doesn't exist yet
            
        # Defensive field mapping
        final_total = getattr(fee_record, 'total_amount', fee_record.final_amount)
        balance = getattr(fee_record, 'balance_amount', final_total)

        return Response({
            'exists': True,
            'fee_id': fee_record.id,
            'total_assigned': float(fee_record.amount_due),
            'concession': float(fee_record.concession_amount),
            'final_total': float(final_total),
            'balance': float(balance),
            'is_paid': fee_record.is_paid,
            'history': [{
                'amount': float(t.amount_paid),
                'method': t.payment_method,
                'date': t.payment_date.strftime('%Y-%m-%d %H:%M'),
                'receipt': t.receipt_number,
                'notes': t.notes
            } for t in transactions]
        })
    except StudentProfile.DoesNotExist:
        return Response({'error': 'Student not found'}, status=404)
    except Exception as e:
        return Response({'exists': False, 'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_payment(request):
    data = request.data
    student_id = data.get('student_id')
    mode = data.get('mode') # 'ASSIGN' or 'PAY'
    
    try:
        student = StudentProfile.objects.get(id=student_id)
        now = timezone.now()
        month_str = now.strftime('%b-%Y')
        
        if mode == 'ASSIGN':
            total_fee = float(data.get('total_fee', 0))
            concession = float(data.get('concession', 0))
            
            # Find or create structure
            class_group = student.student_class.class_group if student.student_class else '1-10'
            structure, _ = FeeStructure.objects.get_or_create(
                class_group=class_group,
                fee_month=month_str,
                defaults={'amount': total_fee, 'due_date': now.date()}
            )
            
            fee_record, created = StudentFee.objects.update_or_create(
                student=student,
                fee_structure=structure,
                defaults={
                    'amount_due': total_fee,
                    'concession_amount': concession,
                }
            )
            # update_or_create save() handles balance_amount for new ones in our updated model
            
            return Response({'success': True, 'message': 'Fee assigned successfully'})
            
        elif mode == 'PAY':
            amount_paid = float(data.get('amount_paid', 0))
            method = data.get('payment_method', 'CASH')
            receipt = data.get('receipt_no', '')
            notes = data.get('notes', '')
            
            fee_record = StudentFee.objects.filter(
                student=student, 
                fee_structure__fee_month=month_str
            ).first()
            
            if not fee_record:
                return Response({'error': 'No fee assigned for this student yet'}, status=400)
            
            # Create transaction
            transaction = FeeTransaction.objects.create(
                student_fee=fee_record,
                amount_paid=amount_paid,
                payment_method=method,
                receipt_number=receipt,
                payment_date=now,
                recorded_by=request.user,
                notes=notes
            )
            
            # Update balance
            fee_record.balance_amount -= Decimal(str(amount_paid))
            # Also update legacy fields for backward compatibility
            fee_record.payment_method = method
            fee_record.payment_date = now
            fee_record.receipt_number = receipt
            fee_record.save()
            
            return Response({
                'success': True, 
                'balance': float(fee_record.balance_amount),
                'receipt_no': transaction.receipt_number
            })
            
    except StudentProfile.DoesNotExist:
        return Response({'error': 'Student not found'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)
