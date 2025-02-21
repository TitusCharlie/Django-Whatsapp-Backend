from celery import shared_task
import requests
from django.conf import settings
from .models import WhatsAppMessage, WhatsAppStatus, Contact, Group
#from .whatsapp_automation import auto_reply_to_message
import logging

logger = logging.getLogger(__name__)

@shared_task
def schedule_whatsapp_message(message_id):
    """Send a WhatsApp message asynchronously using 360Dialog API."""
    try:
        message_obj = WhatsAppMessage.objects.get(id=message_id)

        url = "https://waba.360dialog.io/messages"
        headers = {
            "D360-API-KEY": settings.WHATSAPP_API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "to": message_obj.phone_number,
            "type": "text",
            "text": {"body": message_obj.message}
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            message_obj.status = "Sent"
        else:
            message_obj.status = f"Failed: {response.text}"
            logger.error(f"Failed to send message {message_id}: {response.text}")

        message_obj.save()
        return message_obj.status

    except Exception as e:
        logger.exception(f"Error scheduling message {message_id}: {str(e)}")
        return f"Failed: {str(e)}"

@shared_task
def schedule_whatsapp_status(status_id):
    """Schedule a WhatsApp Status Update using 360Dialog API."""
    try:
        status_obj = WhatsAppStatus.objects.get(id=status_id)

        url = "https://waba.360dialog.io/messages"
        headers = {
            "D360-API-KEY": settings.WHATSAPP_API_KEY,
            "Content-Type": "application/json"
        }

        if status_obj.media:
            payload = {
                "to": "status@broadcast",
                "type": "image",
                "image": {
                    "link": status_obj.media.url,
                    "caption": status_obj.text or ""
                }
            }
        else:
            payload = {
                "to": "status@broadcast",
                "type": "text",
                "text": {"body": status_obj.text}
            }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            status_obj.status = "Posted"
        else:
            status_obj.status = f"Failed: {response.text}"
            logger.error(f"Failed to post status {status_id}: {response.text}")

        status_obj.save()
        return status_obj.status

    except Exception as e:
        logger.exception(f"Error scheduling status {status_id}: {str(e)}")
        return f"Failed: {str(e)}"

@shared_task
def auto_reply_task(phone_number, incoming_message):
    """Auto-reply to an incoming message based on predefined logic."""
    try:
        reply_message = auto_reply_to_message(incoming_message)

        url = "https://waba.360dialog.io/messages"
        headers = {
            "D360-API-KEY": settings.WHATSAPP_API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "to": phone_number,
            "type": "text",
            "text": {"body": reply_message}
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            return "Auto-reply sent successfully"
        else:
            logger.error(f"Failed to send auto-reply to {phone_number}: {response.text}")
            return f"Failed: {response.text}"

    except Exception as e:
        logger.exception(f"Error in auto-reply to {phone_number}: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def fetch_contacts_from_wordpress():
    """Fetch new contacts from a WordPress landing page and assign them to a group."""
    try:
        url = settings.WORDPRESS_CONTACTS_API
        response = requests.get(url)
        response.raise_for_status()
        contacts = response.json()

        for contact_data in contacts:
            phone_number = contact_data.get("phone")
            name = contact_data.get("name", "")

            if not phone_number:
                continue  # Skip invalid entries

            contact, created = Contact.objects.get_or_create(
                phone_number=phone_number, defaults={"name": name}
            )

            if created:
                assign_contact_to_group(contact)

    except requests.RequestException as e:
        logger.error(f"Failed to fetch contacts: {str(e)}")
        return f"Failed: {str(e)}"

def assign_contact_to_group(contact):
    """Assign a contact to an available group, creating new groups if needed."""
    group = Group.objects.filter(is_full=False).first()

    if not group:
        group = Group.objects.create(name=f"Group {Group.objects.count() + 1}")

    contact.group = group
    contact.save()

    # Check if the group is full (limit to 250 contacts)
    if Contact.objects.filter(group=group).count() >= 250:
        group.is_full = True
        group.save()
