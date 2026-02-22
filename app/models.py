from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

# UserProfile Model - Extended user information
class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Hospital Model - For suggesting hospitals
class Hospital(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    lat = models.FloatField()
    lon = models.FloatField()
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    specialization = models.CharField(max_length=200)
    rating = models.FloatField(default=4.5)
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# DetectionHistory Model - Store all detection results
class DetectionHistory(models.Model):
    RESULT_CHOICES = [
        ('healthy', 'Healthy'),
        ('parkinson', 'Parkinson Detected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='detections')
    audio_file = models.FileField(
        upload_to='detection_audios/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['wav', 'mp3', 'webm', 'ogg'])]
    )
    detection_result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    confidence = models.FloatField(help_text="Confidence percentage (0-100)")
    test_date = models.DateTimeField(auto_now_add=True)
    test_type = models.CharField(max_length=20, choices=[('upload', 'Upload'), ('record', 'Record')])
    features_data = models.JSONField(default=dict, blank=True)  # Store extracted features
    
    class Meta:
        ordering = ['-test_date']
        verbose_name_plural = "Detection Histories"

    def __str__(self):
        return f"{self.user.username} - {self.detection_result} ({self.test_date})"


# SuggestedHospital Model - Many-to-Many through model for recommendations
class SuggestedHospital(models.Model):
    detection = models.ForeignKey(DetectionHistory, on_delete=models.CASCADE, related_name='suggested_hospitals')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    rank = models.IntegerField()  # Rank from 1 to 10
    reason = models.TextField(blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['detection', 'hospital']
        ordering = ['rank']

    def __str__(self):
        return f"{self.hospital.name} (Rank: {self.rank})"


# EmailReport Model - Track sent emails
class EmailReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_reports')
    detection = models.OneToOneField(DetectionHistory, on_delete=models.CASCADE, related_name='email_report')
    recipient_email = models.EmailField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('sent', 'Sent'), ('failed', 'Failed'), ('pending', 'Pending')],
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Report for {self.user.username} - {self.status}"
