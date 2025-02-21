from django.contrib import admin
from .models import WhatsAppMessage, Contact, Group

admin.site.register(WhatsAppMessage)
admin.site.register(Contact)
admin.site.register(Group)
