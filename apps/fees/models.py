from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.students.models import StudentProfile
from django.utils import timezone

PAYMENT_METHODS = [
    ('CASH', 'Cash'),
    ('UPI', 'UPI'),
    ('BANK_TRANSFER', 'Bank Transfer'),
    ('CHEQUE', 'Cheque'),
]

class FeeStructure(models.Model):
    class_group = models.CharField(max_length=10)  # '1-2', '3-5', '6-10'
    fee_month = models.CharField(max_length=20)    # 'Jan-2026', 'Feb-2026'
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['class_group', 'fee_month']
    
    def __str__(self):
        return f"{self.class_group} - {self.fee_month} (₹{self.amount})"

class StudentFee(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='fee_records')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2) # This remains as the initial "Total Assigned" for the period
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0) # Final amount after concession
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    concession_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)  # due - concession (legacy, mapping to total_amount)
    is_paid = models.BooleanField(default=False) # True if balance is 0
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        self.total_amount = self.amount_due - self.concession_amount
        self.final_amount = self.total_amount # for backward compatibility
        if not self.pk: # For new records
             self.balance_amount = self.total_amount
        
        if self.balance_amount <= 0:
            self.is_paid = True
        else:
            self.is_paid = False
        super().save(*args, **kwargs)
    
    def __str__(self):
        status = "PAID" if self.is_paid else "PENDING"
        return f"{self.student.roll_number} - {self.fee_structure.fee_month} ({status})"

class ConcessionRequest(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    concession_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ], default='PENDING')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, 
                                  on_delete=models.SET_NULL, related_name='approved_concessions')
    created_at = models.DateTimeField(auto_now_add=True)

class FeeTransaction(models.Model):
    student_fee = models.ForeignKey(StudentFee, on_delete=models.CASCADE, related_name='transactions')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    receipt_number = models.CharField(max_length=50, blank=True)
    payment_date = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Payment of ₹{self.amount_paid} for {self.student_fee.student.roll_number}"
