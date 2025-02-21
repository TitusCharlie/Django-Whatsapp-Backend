import time
import requests
from django.utils.timezone import now
from django.conf import settings
from .models import WhatsAppStatus

def send_whatsapp_message(phone, message):
    """
    Sends a WhatsApp message using the 360Dialog API.
    """
    url = "https://waba.360dialog.io/messages"
    headers = {
        "D360-API-KEY": settings.WHATSAPP_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return "Message Sent Successfully!"
        else:
            return f"Failed: {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def update_whatsapp_status(status_id):
    """
    Updates WhatsApp status using the 360Dialog API.
    """
    status_obj = WhatsAppStatus.objects.get(id=status_id)

    url = "https://waba.360dialog.io/messages"
    headers = {
        "D360-API-KEY": settings.WHATSAPP_API_KEY,
        "Content-Type": "application/json"
    }

    if status_obj.media_url:
        payload = {
            "to": "status@broadcast",
            "type": "image",
            "image": {
                "link": status_obj.media_url,
                "caption": status_obj.caption or ""
            }
        }
    else:
        payload = {
            "to": "status@broadcast",
            "type": "text",
            "text": {"body": status_obj.caption}
        }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            status_obj.posted = True
            status_obj.save()
            print("Status posted successfully!")
        else:
            status_obj.posted = False
            status_obj.save()
            print(f"Failed to post status: {response.text}")
    except Exception as e:
        status_obj.posted = False
        status_obj.save()
        print(f"Error posting status: {str(e)}")