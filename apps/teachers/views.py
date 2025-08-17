# apps/teachers/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import TeacherDashboardSerializer

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
