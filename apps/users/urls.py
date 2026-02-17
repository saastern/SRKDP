from django.urls import path
from .views import login_view, profile_view, logout_view

app_name = 'users'
urlpatterns = [
    path('login/', login_view, name='login'),
    path('profile/', profile_view, name='profile'),
    path('logout/', logout_view, name='logout'),
    path('debug/', profile_view, name='debug_auth'),  # Using profile_view for debug too
    path('api/auth/debug/', profile_view, name='api_auth_debug'), # New endpoint to check authentication status
]
