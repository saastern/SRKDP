from rest_framework import serializers
from django.db.models import Sum, Avg, Count
from .models import *
from apps.students.models import StudentProfile, Class

class ClassSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    class Meta:
        model = Class
        fields = ['id', 'name', 'display_name', 'class_group', 'student_count', 'class_group']

    def get_student_count(self, obj):
        return obj.studentprofile_set.count()
    
    def get_display_name(self, obj):
        return obj.name

class StudentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    roll_no = serializers.CharField(source='roll_number')
    class_name = serializers.CharField(source='student_class.name')

    class Meta:
        model = StudentProfile
        fields = ['id', 'name', 'roll_no', 'class_name']
    
    def get_name(self, obj):
        return obj.user.get_full_name() or f"Student {obj.roll_number}"

class SubjectMarkDetailSerializer(serializers.Serializer):
    marks = serializers.DecimalField(max_digits=5, decimal_places=2)
    grade = serializers.CharField()
    max_marks = serializers.IntegerField()

class SubjectSerializer(serializers.Serializer):
    name = serializers.CharField()
    fa1 = SubjectMarkDetailSerializer()
    fa2 = SubjectMarkDetailSerializer()
    fa3 = SubjectMarkDetailSerializer()
    fa4 = SubjectMarkDetailSerializer()
    sa1 = SubjectMarkDetailSerializer()
    sa2 = SubjectMarkDetailSerializer()

class TermSummarySerializer(serializers.Serializer):
    term = serializers.CharField()
    total_marks = serializers.IntegerField()
    max_marks = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    grade = serializers.CharField()
    class_rank = serializers.IntegerField()
    total_students = serializers.IntegerField()

class ClassConfigSerializer(serializers.ModelSerializer):
    fa_marks = serializers.IntegerField()
    sa_marks = serializers.IntegerField()
    exclude_from_total = serializers.ListField()
    grading_scale = serializers.CharField()

class StudentMarksDetailSerializer(serializers.Serializer):
    student = StudentSerializer()
    subjects = SubjectSerializer(many=True)
    term_summaries = TermSummarySerializer(many=True)
    class_config = ClassConfigSerializer()