# apps/notifications/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Announcement

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def announcements_list_create(request):
    """
    GET: List all announcements
    POST: Create a new announcement (principal/admin only)
    """
    if request.method == 'GET':
        announcements = Announcement.objects.all().select_related('created_by')
        data = [{
            'id': a.id,
            'title': a.title,
            'message': a.message,
            'created_by': a.created_by.get_full_name() or a.created_by.username,
            'target_role': a.target_role,
            'is_pinned': a.is_pinned,
            'created_at': a.created_at.strftime('%Y-%m-%d %H:%M'),
        } for a in announcements]
        return Response({'success': True, 'announcements': data})
    
    # POST: Create new announcement
    if request.user.role not in ['principal', 'admin']:
        return Response({'error': 'Only principals or admins can create announcements'}, status=403)
    
    title = request.data.get('title', '').strip()
    message = request.data.get('message', '').strip()
    target_role = request.data.get('target_role', 'all')
    is_pinned = request.data.get('is_pinned', False)
    
    if not title or not message:
        return Response({'error': 'Title and message are required'}, status=400)
    
    announcement = Announcement.objects.create(
        title=title,
        message=message,
        created_by=request.user,
        target_role=target_role,
        is_pinned=is_pinned,
    )
    
    return Response({
        'success': True,
        'message': 'Announcement created successfully',
        'announcement': {
            'id': announcement.id,
            'title': announcement.title,
            'message': announcement.message,
            'created_by': request.user.get_full_name() or request.user.username,
            'target_role': announcement.target_role,
            'is_pinned': announcement.is_pinned,
            'created_at': announcement.created_at.strftime('%Y-%m-%d %H:%M'),
        }
    }, status=201)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_announcement(request, announcement_id):
    """Delete an announcement"""
    if request.user.role not in ['principal', 'admin']:
        return Response({'error': 'Unauthorized'}, status=403)
    
    try:
        announcement = Announcement.objects.get(id=announcement_id)
        announcement.delete()
        return Response({'success': True, 'message': 'Announcement deleted'})
    except Announcement.DoesNotExist:
        return Response({'error': 'Announcement not found'}, status=404)
