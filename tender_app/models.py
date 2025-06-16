# tender_app/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

class TenderProject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error')
    ], default='pending')

    def __str__(self):
        return self.name

class TenderTemplate(models.Model):
    project = models.ForeignKey(TenderProject, on_delete=models.CASCADE)
    file = models.FileField(upload_to='templates/')
    title = models.CharField(max_length=200, blank=True)
    file_type = models.CharField(max_length=10, choices=[
        ('docx', 'Word Document'),
        ('pdf', 'PDF Document'),
        ('xlsx', 'Excel Spreadsheet')
    ])
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class ReferenceDocument(models.Model):
    project = models.ForeignKey(TenderProject, on_delete=models.CASCADE)
    file = models.FileField(upload_to='references/')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class ExtractedField(models.Model):
    template = models.ForeignKey(TenderTemplate, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=200)
    field_type = models.CharField(max_length=50)
    position_info = models.JSONField()  # Store position/location data
    generated_content = models.TextField(blank=True)
    is_filled = models.BooleanField(default=False)

class ProcessedDocument(models.Model):
    project = models.ForeignKey(TenderProject, on_delete=models.CASCADE)
    file = models.FileField(upload_to='processed/')
    created_at = models.DateTimeField(auto_now_add=True)
