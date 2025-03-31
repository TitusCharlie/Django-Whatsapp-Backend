from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class WhatsAppGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    landing_page = models.CharField(max_length=255)  # Identifies where contacts come from
    max_capacity = models.IntegerField(default=250)  # WhatsApp group size limit
    created_at = models.DateTimeField(auto_now_add=True)

    def current_size(self):
        return self.contacts.count()

    def is_full(self):
        return self.current_size() >= self.max_capacity

    def __str__(self):
        return f"{self.name} ({self.current_size()}/{self.max_capacity})"

class Contact(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True)
    landing_page = models.CharField(max_length=255)  # Links to the correct group
    group = models.ForeignKey(WhatsAppGroup, on_delete=models.SET_NULL, null=True, related_name="contacts")
    created_at = models.DateTimeField(auto_now_add=True)

    def assign_to_group(self):
        """Assigns the contact to an available group or creates a new one."""
        existing_group = WhatsAppGroup.objects.filter(landing_page=self.landing_page).order_by('-created_at').first()
        
        if existing_group and not existing_group.is_full():
            self.group = existing_group
        else:
            new_group = WhatsAppGroup.objects.create(
                name=f"{self.landing_page} Group {WhatsAppGroup.objects.filter(landing_page=self.landing_page).count() + 1}",
                landing_page=self.landing_page
            )
            self.group = new_group
        
        self.save()

    def __str__(self):
        return f"{self.name} - {self.phone_number} ({self.landing_page})"

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

    def is_scheduled(self):
        return self.scheduled_at is not None and self.scheduled_at > timezone.now()