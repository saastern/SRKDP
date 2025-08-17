from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Teacher login endpoint - authenticates using username
    """
    # Add debug logging
    logger.info(f"Login attempt received")
    logger.info(f"Request data: {request.data}")
    logger.info(f"Content type: {request.content_type}")
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    logger.info(f"Extracted username: '{username}', password length: {len(password) if password else 0}")
    
    if not username or not password:
        logger.warning("Missing username or password")
        return Response({
            'success': False,
            'message': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if user exists in database first
    try:
        user_exists = User.objects.get(username=username)
        logger.info(f"Found user: {user_exists.username}, role: {user_exists.role}")
    except User.DoesNotExist:
        logger.error(f"User '{username}' does not exist in database")
        return Response({
            'success': False,
            'message': 'Invalid username or password'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Try authentication
    user = authenticate(request, username=username, password=password)
    logger.info(f"Authentication result: {user}")
    
    if not user:
        logger.error(f"Authentication failed for user: {username}")
        return Response({
            'success': False,
            'message': 'Invalid username or password'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if user is a teacher
    if user.role != 'teacher':
        logger.warning(f"Non-teacher user attempted login: {user.role}")
        return Response({
            'success': False,
            'message': 'Access restricted to teachers only'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    logger.info(f"Login successful for user: {username}")
    
    return Response({
        'success': True,
        'message': 'Login successful',
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'role': user.role
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    Get current authenticated user's profile
    """
    return Response({
        'success': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'full_name': request.user.get_full_name(),
            'role': request.user.role
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout endpoint - blacklist the refresh token
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'success': True,
            'message': 'Logout successful'
        })
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)
