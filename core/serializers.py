from rest_framework import serializers
from .models import Contact, WhatsAppMessage, WhatsAppStatus, WhatsAppGroup

class WhatsAppGroupSerializer(serializers.ModelSerializer):
    current_size = serializers.SerializerMethodField()

    class Meta:
        model = WhatsAppGroup
        fields = ['id', 'name', 'landing_page', 'max_capacity', 'current_size', 'created_at']

    def get_current_size(self, obj):
        return obj.current_size()

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'phone_number', 'landing_page', 'group', 'created_at']

class WhatsAppMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppMessage
        fields = '__all__'
        read_only_fields = ['user', 'status']

class WhatsAppStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppStatus
        fields = '__all__'
        read_only_fields = ['user', 'status']
