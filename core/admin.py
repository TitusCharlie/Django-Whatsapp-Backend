from django.contrib import admin
from .models import WhatsAppMessage, Contact, WhatsAppGroup

admin.site.register(WhatsAppMessage)
admin.site.register(Contact)
admin.site.register(WhatsAppGroup)