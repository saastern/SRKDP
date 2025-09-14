from django.core.management.base import BaseCommand
from apps.assessments.models import Subject, AcademicYear, ClassSubjectMapping
from apps.students.models import Class

DEFAULT_SUBJECTS = {
    '8-10': {
        'main': ['Telugu', 'Hindi', 'English', 'Mathematics', 'Physical Science', 'Natural Science', 'Social'],
        'optional': [],  # No optional by default for 8-10
    },
    '6-7': {
        'main': ['Telugu', 'Hindi', 'English', 'Mathematics', 'Science', 'Social'],
        'optional': ['GK', 'Computer'],
    },
    '3-5': {
        'main': ['Telugu', 'Hindi', 'English', 'Mathematics', 'Science', 'Social'],
        'optional': ['GK', 'Computer'],
    },
    '1-2': {
        'main': ['Telugu', 'Hindi', 'English', 'Mathematics', 'EVS'],
        'optional': ['GK'],
    },
    'pre': {
        'main': ['Telugu', 'English', 'Mathematics', 'Color', 'EVS'],
        'optional': [],
    },
}

class Command(BaseCommand):
    help = 'Create subject mappings based on exact school requirements'
    
    def handle(self, *args, **options):
        # Clear existing mappings first
        ClassSubjectMapping.objects.all().delete()
        self.stdout.write("🗑️ Cleared existing mappings")
        
        academic_year = AcademicYear.objects.filter(is_current=True).first()
        if not academic_year:
            self.stdout.write(self.style.ERROR('❌ No current academic year found'))
            return
        
        total_mappings = 0
        
        for class_obj in Class.objects.all():
            group = class_obj.class_group
            
            if group not in DEFAULT_SUBJECTS:
                self.stdout.write(f"⚠️  No subjects for class group '{group}' (Class: {class_obj.name})")
                continue
            
            # Get subjects for this group
            main_subject_names = DEFAULT_SUBJECTS[group]['main']
            optional_subject_names = DEFAULT_SUBJECTS[group]['optional'].copy()  # Make a copy
            
            # Special handling for UKG (add Hindi to main subjects)
            if class_obj.name.upper() == 'UKG':
                main_subject_names = main_subject_names + ['Hindi']
            
            # Special handling for Class 8 ONLY (add GK as optional)
            if class_obj.name.startswith('8'):
                optional_subject_names = optional_subject_names + ['GK']
                self.stdout.write(f"📝 Adding GK as optional for {class_obj.name}")
            
            # Create main subject mappings
            main_subjects = Subject.objects.filter(name__in=main_subject_names)
            for subject in main_subjects:
                ClassSubjectMapping.objects.create(
                    student_class=class_obj,
                    subject=subject,
                    academic_year=academic_year,
                    is_main_subject=True
                )
                total_mappings += 1
                self.stdout.write(f"✅ {class_obj.name} -> {subject.name} (Main)")
            
            # Create optional subject mappings
            optional_subjects = Subject.objects.filter(name__in=optional_subject_names)
            for subject in optional_subjects:
                ClassSubjectMapping.objects.create(
                    student_class=class_obj,
                    subject=subject,
                    academic_year=academic_year,
                    is_main_subject=False
                )
                total_mappings += 1
                self.stdout.write(f"✅ {class_obj.name} -> {subject.name} (Optional)")
        
        self.stdout.write(self.style.SUCCESS(f'🎉 Created {total_mappings} subject mappings!'))
        
        # Summary
        self.stdout.write("\n📊 Summary:")
        for group in ['pre', '1-2', '3-5', '6-7', '8-10']:
            count = ClassSubjectMapping.objects.filter(
                student_class__class_group=group,
                academic_year=academic_year
            ).count()
            self.stdout.write(f"  {group}: {count} mappings")
