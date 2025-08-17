from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

class LoginSerializer(serializers.Serializer):
    """
    Serializer for teacher login using email/password
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            # Try to find user by email
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    if user.role == 'teacher':
                        data['user'] = user
                        return data
                    else:
                        raise serializers.ValidationError('Access restricted to teachers only')
                else:
                    raise serializers.ValidationError('Invalid credentials')
            except User.DoesNotExist:
                raise serializers.ValidationError('Invalid credentials')
        else:
            raise serializers.ValidationError('Email and password are required')

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user data
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'role']
