from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django import forms
import csv
import io
from .models import User
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile

# CSV Import Form
class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label='Select CSV file')

# Your existing inline classes
class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fk_name = 'user'

class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    can_delete = False
    verbose_name_plural = 'Teacher Profile'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (('Custom Fields', {'fields': ('role',)}),)
    list_display = BaseUserAdmin.list_display + ('role',)
    list_filter = BaseUserAdmin.list_filter + ('role',)
    
    # Add custom actions dropdown
    actions = ['export_users_to_csv']

    def get_inline_instances(self, request, obj=None):
        inlines = []
        if obj:
            if obj.role == 'student':
                inlines = [StudentProfileInline(self.model, self.admin_site)]
            elif obj.role == 'teacher':
                inlines = [TeacherProfileInline(self.model, self.admin_site)]
        return inlines

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='import_csv'),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                data_set = csv_file.read().decode('UTF-8')
                io_string = io.StringIO(data_set)
                reader = csv.DictReader(io_string)
                
                from apps.students.models import Class  # Import here
                
                created_count = 0
                skipped_count = 0
                errors = []
                
                for row_num, row in enumerate(reader, start=2):
                    username = row.get('username', '').strip()
                    
                    if not username:
                        skipped_count += 1
                        errors.append(f"Row {row_num}: Missing username - skipped")
                        continue
                    
                    try:
                        user, is_new = User.objects.get_or_create(
                            username=username,
                            defaults={
                                'first_name': row.get('first_name', '').strip(),
                                'last_name': row.get('last_name', '').strip(),
                                'email': row.get('email', '').strip(),
                                'role': row.get('role', 'student').strip() or 'student',
                            }
                        )
                        
                        # Set password if provided
                        password = row.get('password', '').strip()
                        if password and is_new:
                            user.set_password(password)
                            user.save()
                        
                        # Create related profiles based on role
                        if is_new:
                            if user.role == 'student':
                                # Create StudentProfile
                                class_name = row.get('class_name', '').strip()
                                student_class = None
                                
                                if class_name:
                                    student_class, _ = Class.objects.get_or_create(name=class_name)
                                
                                StudentProfile.objects.create(
                                    user=user,
                                    student_class=student_class,
                                    roll_number=row.get('roll_number', '').strip(),
                                    mother_phone=row.get('mother_phone', '').strip(),
                                    father_phone=row.get('father_phone', '').strip(),
                                )
                            
                            elif user.role == 'teacher':
                                # Create TeacherProfile
                                TeacherProfile.objects.create(
                                    user=user,
                                    subjects=row.get('subjects', '').strip(),
                                )
                            
                            created_count += 1
                            
                    except Exception as e:
                        skipped_count += 1
                        errors.append(f"Row {row_num}: {str(e)}")
                
                if created_count > 0:
                    messages.success(request, f'Successfully imported {created_count} users with profiles!')
                if skipped_count > 0:
                    messages.warning(request, f'Skipped {skipped_count} rows due to errors.')
                if errors:
                    messages.error(request, 'Errors: ' + '; '.join(errors[:5]))
                    
                return redirect('../')
        else:
            form = CsvImportForm()
        
        return render(request, 'admin/csv_import.html', {'form': form})


    def export_users_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['username', 'first_name', 'last_name', 'email', 'role'])
        
        for user in queryset:
            writer.writerow([user.username, user.first_name, user.last_name, user.email, user.role])
        
        return response
    export_users_to_csv.short_description = "Export selected users to CSV"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_csv_url'] = 'import-csv/'
        return super().changelist_view(request, extra_context)

admin.site.register(User, UserAdmin)
