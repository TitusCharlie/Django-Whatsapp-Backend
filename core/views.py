from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
import requests
from django.conf import settings
from .models import Contact, WhatsAppMessage, WhatsAppStatus, Group
from .serializers import ContactSerializer, WhatsAppMessageSerializer, WhatsAppStatusSerializer, GroupSerializer
from .tasks import schedule_whatsapp_message, schedule_whatsapp_status, fetch_contacts_from_wordpress

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def fetch_from_wordpress(self, request):
        """Trigger fetching contacts from a WordPress landing page."""
        fetch_contacts_from_wordpress.delay()
        return Response({"message": "Fetching contacts..."})

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get groups that are not full."""
        available_groups = self.queryset.filter(is_full=False)
        serializer = self.get_serializer(available_groups, many=True)
        return Response(serializer.data)

class WhatsAppMessageViewSet(viewsets.ModelViewSet):
    queryset = WhatsAppMessage.objects.all()
    serializer_class = WhatsAppMessageSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return queryset

    def perform_create(self, serializer):
        message_obj = serializer.save(user=self.request.user)
        if message_obj.scheduled_at:
            schedule_whatsapp_message.apply_async((message_obj.id,), eta=message_obj.scheduled_at)
        else:
            schedule_whatsapp_message.delay(message_obj.id)

class WhatsAppStatusViewSet(viewsets.ModelViewSet):
    queryset = WhatsAppStatus.objects.all()
    serializer_class = WhatsAppStatusSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return queryset

    def perform_create(self, serializer):
        status_obj = serializer.save(user=self.request.user)
        if not status_obj.scheduled_at:
            schedule_whatsapp_status.delay(status_obj.id)
