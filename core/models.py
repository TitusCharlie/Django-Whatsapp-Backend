from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Group(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_full = models.BooleanField(default=False)
    whatsapp_group_link = models.URLField(blank=True, null=True)  # Invite link
    max_contacts = models.IntegerField(default=256)  # Default WhatsApp group limit

    def __str__(self):
        return self.name
    
    def check_if_full(self):
        """Check if the group has reached the max number of contacts."""
        if self.contact_set.count() >= self.max_contacts:
            self.is_full = True
            self.save()

class Contact(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)  # Owner of the contact
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)  # Assigned WhatsApp group

    def __str__(self):
        return self.name

class WhatsAppMessage(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Sent', 'Sent'),
        ('Failed', 'Failed')
    ]

    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"To {self.phone_number}: {self.message[:20]}"

    def is_scheduled(self):
        return self.scheduled_at is not None and self.scheduled_at > timezone.now()

class WhatsAppStatus(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Posted', 'Posted'),
        ('Failed', 'Failed')
    ]
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    text = models.CharField(max_length=255, blank=True, null=True)
    media = models.FileField(upload_to='status_media/', blank=True, null=True)  # For images/videos
    scheduled_at = models.DateTimeField(blank=True, null=True)  # Optional scheduling
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Status by {self.user.username} at {self.scheduled_at or self.created_at}"
