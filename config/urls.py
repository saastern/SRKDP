
from django.contrib import admin
from django.urls import path,include
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


 # Optional custom index
@csrf_exempt  
def health_check(request):
    return HttpResponse("OK", status=200, content_type='text/plain')


def home_view(request):
    return HttpResponse("School SaaS API is running!")



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),

    path('api/auth/', include('apps.users.urls')),
    path('health/', health_check, name='health_with_slash'),
    path('health', health_check, name='health_without_slash'),  
     path('assessments/', include('apps.assessments.urls')),
    path('api/teachers/', include('apps.teachers.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('', include('apps.assessments.urls')),
    path('', include('apps.attendance.urls')),
    path('fees/', include('apps.fees.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh')


]  

