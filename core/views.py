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

    def create(self, request, *args, **kwargs):
        """Create a new contact from WordPress or manual input."""
        name = request.data.get("Name") or request.data.get("name")
        phone_number = request.data.get("tel-463") or request.data.get("phone_number")

        if not name or not phone_number:
            return Response({"error": "Name and phone number are required."}, status=400)

        contact, created = Contact.objects.get_or_create(name=name, phone_number=phone_number)
        serializer = self.get_serializer(contact)
        return Response(serializer.data, status=201 if created else 200)

    @action(detail=False, methods=['post'])
    def fetch_from_wordpress(self, request):
        """Fetch contacts from WordPress API and save them."""
        wordpress_url = "https://skillelearn.online/wp-json/wp/v2/contact_form_entries"
        response = requests.get(wordpress_url)

        if response.status_code != 200:
            return Response({"error": "Failed to fetch contacts from WordPress."}, status=response.status_code)

        contacts = response.json()
        for entry in contacts:
            name = entry.get("Name")
            phone_number = entry.get("tel-463")
            if name and phone_number:
                Contact.objects.get_or_create(name=name, phone_number=phone_number)

        return Response({"message": "Contacts fetched successfully."}, status=200)


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
