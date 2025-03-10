from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions,serializers
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
import requests, logging
from django.conf import settings
from .models import Contact, WhatsAppMessage, WhatsAppStatus, Group
from .serializers import ContactSerializer, WhatsAppMessageSerializer, WhatsAppStatusSerializer, GroupSerializer
from .tasks import schedule_whatsapp_message, schedule_whatsapp_status, fetch_contacts_from_wordpress

logger = logging.getLogger(__name__)
# class ContactViewSet(viewsets.ModelViewSet):
#     queryset = Contact.objects.all()
#     serializer_class = ContactSerializer

#     def get_queryset(self):
#         """Return all contacts without filtering by user."""
#         return Contact.objects.all()  # Removed filtering by self.request.user

#     def perform_create(self, serializer):
#         # Log the request data for debugging
#         logger.info(f"Received Data: {self.request.data}")

#         # Extract fields with correct names from WordPress
#         name = self.request.data.get("Name")  # Matches "Name" from WordPress
#         phone_number = self.request.data.get("tel-463")  # Matches "tel-463" from WordPress

#         # Check if the required fields exist
#         if not name or not phone_number:
#             raise serializers.ValidationError({"name": ["This field is required."], "phone_number": ["This field is required."]})

#         serializer.save(name=name, phone_number=phone_number)
 
#     @action(detail=False, methods=['post'])
#     def fetch_from_wordpress(self, request):
#         """Trigger fetching contacts from a WordPress landing page."""
#         fetch_contacts_from_wordpress.delay()
#         return Response({"message": "Fetching contacts..."})

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def perform_create(self, serializer):
        # Print and log raw request body
        raw_body = self.request.body.decode("utf-8")
        print(f"DEBUG LOG: Raw Request Body = {raw_body}")
        logger.info(f"DEBUG LOG: Raw Request Body = {raw_body}")

        # Ensure request data exists
        if not self.request.data:
            raise serializers.ValidationError({"error": "No data received. Ensure you are sending JSON with the correct fields."})

        # Extract fields
        name = self.request.data.get("Name")
        phone_number = self.request.data.get("tel-463")

        print(f"DEBUG LOG: Extracted Name = {name}, Phone = {phone_number}")
        logger.info(f"DEBUG LOG: Extracted Name = {name}, Phone = {phone_number}")

        # Validate required fields
        if not name or not phone_number:
            raise serializers.ValidationError({"name": "This field is required.", "phone_number": "This field is required."})

        serializer.save(name=name, phone_number=phone_number)

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = []

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get groups that are not full."""
        available_groups = self.queryset.filter(is_full=False)
        serializer = self.get_serializer(available_groups, many=True)
        return Response(serializer.data)

class WhatsAppMessageViewSet(viewsets.ModelViewSet):
    queryset = WhatsAppMessage.objects.all()
    serializer_class = WhatsAppMessageSerializer
    # permission_classes = []

    def get_queryset(self):
        return self.queryset

    def perform_create(self, serializer):
        message_obj = serializer.save()
        # message_obj = serializer.save(user=self.request.user)
        # if message_obj.scheduled_at:
        #     schedule_whatsapp_message.apply_async((message_obj.id,), eta=message_obj.scheduled_at)
        # else:
        #     schedule_whatsapp_message.delay(message_obj.id)
        if message_obj.scheduled_at:
            schedule_whatsapp_message(message_obj.id)
        else:
            schedule_whatsapp_message(message_obj.id)

class WhatsAppStatusViewSet(viewsets.ModelViewSet):
    queryset = WhatsAppStatus.objects.all()
    serializer_class = WhatsAppStatusSerializer
    # permission_classes = []

    def get_queryset(self):
        return self.queryset

    def perform_create(self, serializer):
        status_obj = serializer.save()
        # status_obj = serializer.save(user=self.request.user)
        if not status_obj.scheduled_at:
            # schedule_whatsapp_status.delay(status_obj.id)
            schedule_whatsapp_status(status_obj.id)
