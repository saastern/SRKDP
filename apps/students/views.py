from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import StudentProfile
from django.db.models import Q

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_students(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response({'success': False, 'message': 'Query too short'}, status=400)
    
    students = StudentProfile.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(roll_number__icontains=query)
    ).select_related('user', 'student_class')[:10]
    
    results = []
    for s in students:
        results.append({
            'id': s.id,
            'full_name': f"{s.user.first_name} {s.user.last_name}",
            'roll_number': s.roll_number,
            'class_name': s.student_class.name if s.student_class else 'N/A'
        })
        
    return Response({'success': True, 'students': results})
