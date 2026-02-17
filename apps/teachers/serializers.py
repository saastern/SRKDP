# apps/teachers/serializers.py
from rest_framework import serializers
from apps.students.models import Class
from apps.users.models import User

class ClassWithStudentCountSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = ['id', 'name', 'student_count']
    
    def get_student_count(self, obj):
        # Updated to use the correct field name
        return obj.studentprofile_set.count()

class TeacherDashboardSerializer(serializers.ModelSerializer):
    all_classes = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'all_classes']
    
    def get_all_classes(self, obj):
        # Get ALL classes in the database
        all_classes = Class.objects.all() # Meta ordering
        return ClassWithStudentCountSerializer(all_classes, many=True).data
