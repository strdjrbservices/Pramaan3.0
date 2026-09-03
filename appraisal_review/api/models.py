from django.db import models
from django.contrib.auth.models import User
import uuid

class UploadedFile(models.Model):
    """
    Represents a file uploaded by a user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File '{self.file.name}' uploaded by {self.user.username}"
class AppraisalReport(models.Model):
    """
    Stores the JSON data for a single appraisal report.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_name = models.CharField(max_length=255, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    report_data = models.JSONField()
    validation_log = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=50, default='Completed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        Returns a human-readable representation of the report.
        """
        try:
            subject_data = self.report_data.get('Subject', {})
            if not subject_data: 
                 subject_data = self.report_data.get('SUBJECT', {})

            property_address = subject_data.get('Property Address', 'N/A')
            borrower = subject_data.get('Borrower', 'N/A')
            base_str = f"Report for {property_address} ({borrower})"
            if self.file_name:
                base_str += f" - {self.file_name}"
            return f"{base_str} created at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        except Exception:
            return f"Report ID: {self.id}"

    class Meta:
        ordering = ['-created_at']


class ContactMessage(models.Model):
    """
    Stores contact form submissions.
    """
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    send_copy = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}: {self.subject}"