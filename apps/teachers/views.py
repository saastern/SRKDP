# apps/teachers/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import TeacherDashboardSerializer
from .models import TeacherProfile
from apps.users.models import User

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_dashboard(request):
    print("\n" + "="*50)
    print("TEACHER DASHBOARD ENDPOINT HIT")
    print("User authenticated:", request.user.is_authenticated)
    print("User ID:", request.user.id)
    print("Username:", request.user.username)
    print("Role:", repr(request.user.role))
    print("="*50 + "\n")

    if request.user.role != "teacher":
        return Response(
            {"success": False,
             "message": f"Access restricted to teachers only (role seen: {request.user.role!r})"},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = TeacherDashboardSerializer(request.user)
    return Response({"success": True, "teacher": serializer.data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_teachers(request):
    """List all teachers for Principal view"""
    if request.user.role not in ['principal', 'admin']:
        return Response({'error': 'Unauthorized'}, status=403)
        
    teachers = TeacherProfile.objects.all().select_related('user')
    results = []
    for t in teachers:
        results.append({
            'id': t.id,
            'user_id': t.user.id,
            'name': t.user.get_full_name() or t.user.username,
            'username': t.user.username,
            'email': t.user.email,
            'subjects': t.subjects,
            'role': 'Faculty',
            'is_active': t.user.is_active
        })
    return Response({'success': True, 'staff': results})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_staff(request):
    """Add a new staff member (creates User + TeacherProfile)"""
    if request.user.role not in ['principal', 'admin']:
        return Response({'error': 'Unauthorized'}, status=403)
    
    data = request.data
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    subjects = data.get('subjects', '').strip()
    
    if not username or not password:
        return Response({'error': 'Username and password are required'}, status=400)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': f'Username "{username}" already exists'}, status=400)
    
    try:
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role='teacher'
        )
        
        profile = TeacherProfile.objects.create(
            user=user,
            subjects=subjects or 'General'
        )
        
        return Response({
            'success': True,
            'message': f'Staff member {first_name} {last_name} added successfully',
            'staff': {
                'id': profile.id,
                'user_id': user.id,
                'name': user.get_full_name(),
                'username': user.username,
                'email': user.email,
                'subjects': profile.subjects
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_staff(request, staff_id):
    """Update a staff member's details"""
    if request.user.role not in ['principal', 'admin']:
        return Response({'error': 'Unauthorized'}, status=403)
    
    try:
        profile = TeacherProfile.objects.get(id=staff_id)
        user = profile.user
        data = request.data
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            user.email = data['email']
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        if 'subjects' in data:
            profile.subjects = data['subjects']
        
        user.save()
        profile.save()
        
        return Response({
            'success': True,
            'message': 'Staff updated successfully',
            'staff': {
                'id': profile.id,
                'name': user.get_full_name(),
                'username': user.username,
                'email': user.email,
                'subjects': profile.subjects
            }
        })
    except TeacherProfile.DoesNotExist:
        return Response({'error': 'Staff member not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_staff(request, staff_id):
    """Delete a staff member (removes User and TeacherProfile)"""
    if request.user.role not in ['principal', 'admin']:
        return Response({'error': 'Unauthorized'}, status=403)
    
    try:
        profile = TeacherProfile.objects.get(id=staff_id)
        user = profile.user
        name = user.get_full_name()
        
        # Delete profile and user
        profile.delete()
        user.delete()
        
        return Response({
            'success': True,
            'message': f'Staff member {name} deleted successfully'
        })
    except TeacherProfile.DoesNotExist:
        return Response({'error': 'Staff member not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
