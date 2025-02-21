"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""
import os
import django
from django.core.asgi import get_asgi_application
import socketio
from socketio import ASGIApp

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# Initialize Socket.IO server
sio = socketio.Server(async_mode="threading", cors_allowed_origins="*")

# Django ASGI app
django_asgi_app = get_asgi_application()

# Wrap Django ASGI with Socket.IO
application = ASGIApp(sio, django_asgi_app)

# Event handlers for WebSocket connections
@sio.event
def connect(sid, environ):
    print(f"Client {sid} connected")

@sio.event
def disconnect(sid):
    print(f"Client {sid} disconnected")

# Function to emit new messages
def send_new_message(data):
    sio.emit("new_message", data)

