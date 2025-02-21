from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContactViewSet, 
    WhatsAppMessageViewSet, 
    WhatsAppStatusViewSet, 
    GroupViewSet, 
    fetch_contacts_from_wordpress
)

router = DefaultRouter()
router.register(r'contacts', ContactViewSet)
router.register(r'whatsapp', WhatsAppMessageViewSet)
router.register(r'status', WhatsAppStatusViewSet)
router.register(r'groups', GroupViewSet)  # Group API

urlpatterns = [
    path('', include(router.urls)),  # Include all viewsets
    path('fetch-contacts/', fetch_contacts_from_wordpress, name='fetch-contacts'),  # Fetch contacts from WordPress
]
