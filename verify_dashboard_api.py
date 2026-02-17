import os
import django
import sys

# Set up Django environment
sys.path.append('c:\\Users\\Rohith\\Desktop\\school_saas')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.dashboard.views import principal_dashboard_summary
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.users.models import User

def verify_api():
    factory = APIRequestFactory()
    user = User.objects.filter(role='principal').first()
    if not user:
        user = User.objects.create_user(username='test_principal', password='password', role='principal')
    
    request = factory.get('/api/dashboard/api/principal/summary/')
    force_authenticate(request, user=user)
    
    response = principal_dashboard_summary(request)
    print(f"Status Code: {response.status_code}")
    print(f"Response Data: {response.data}")
    
    if response.status_code == 200 and response.data['success']:
        print("✅ API Verification Successful!")
        return True
    else:
        print("❌ API Verification Failed!")
        return False

if __name__ == "__main__":
    verify_api()
