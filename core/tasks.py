from celery import shared_task
import requests
from django.conf import settings
from .models import WhatsAppMessage, WhatsAppStatus, Contact, WhatsAppGroup
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
    """Fetch new contacts from WordPress and assign them to the right WhatsApp group."""
    try:
        url = settings.WORDPRESS_CONTACTS_API
        response = requests.get(url)
        response.raise_for_status()
        contacts = response.json()

        for contact_data in contacts:
            phone_number = contact_data.get("phone")
            name = contact_data.get("name", "")
            group_id = contact_data.get("group_id")  # Ensure WordPress includes this

            if not phone_number or not group_id:
                continue  # Skip invalid entries

            contact, created = Contact.objects.get_or_create(
                phone_number=phone_number, defaults={"name": name}
            )

            if created:
                assign_contact_to_group(contact, group_id)

    except requests.RequestException as e:
        logger.error(f"Failed to fetch contacts: {str(e)}")
        return f"Failed: {str(e)}"

def assign_contact_to_group(contact, group_id):
    """Assign a contact to the correct WhatsApp group based on group_id."""
    group = WhatsAppGroup.objects.filter(landing_page_id=group_id, is_full=False).first()

    if not group:
        group = WhatsAppGroup.objects.create(name=f"Group {WhatsAppGroup.objects.count() + 1}", landing_page_id=group_id)

    contact.group = group
    contact.save()

    # Send the contact to WhatsApp
    send_contact_to_whatsapp(contact, group)

    # Mark group as full if it reaches 250 members
    if Contact.objects.filter(group=group).count() >= 250:
        group.is_full = True
        group.save()

def send_contact_to_whatsapp(contact, group):
    """Send a contact's phone number to the correct WhatsApp group."""
    if not group.whatsapp_id:
        logger.warning(f"Group {group.id} does not have a WhatsApp ID.")
        return

    url = f"https://waba.360dialog.io/v1/groups/{group.whatsapp_id}/add"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {"phone_number": contact.phone_number}

    try:
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("success"):
            logger.info(f"Successfully added {contact.phone_number} to {group.name}")
        else:
            logger.error(f"Failed to add {contact.phone_number}: {response_data}")

    except requests.RequestException as e:
        logger.error(f"Error sending contact to WhatsApp: {str(e)}")