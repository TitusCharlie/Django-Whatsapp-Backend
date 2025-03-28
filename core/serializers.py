from rest_framework import serializers
from .models import Contact, WhatsAppMessage, WhatsAppStatus, Group

class GroupSerializer(serializers.ModelSerializer):
    contacts = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = '__all__'

    def get_contacts(self, obj):
        """Return the contacts belonging to this group."""
        contacts = obj.contact_set.all()
        return ContactSerializer(contacts, many=True).data

class ContactSerializer(serializers.ModelSerializer):
    # group = GroupSerializer(read_only=True)

    class Meta:
        model = Contact
        fields = ["name", "phone_number"]

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
