import pywebpush
from django.conf import settings
from typing import TypedDict, Literal
from datetime import datetime
from django.http import HttpRequest
import json
from django.contrib import messages

from .models import Client, Achievement

class NotificationAction(TypedDict):
    action: str
    title: str
    navigate: str
    icon: str

class Notification(TypedDict):
    title: str
    dir: Literal["auto"] | Literal["ltr"] | Literal["rtl"]
    lang: str
    body: str
    navigate: str
    tag: str
    image: str
    icon: str
    badge: str
    timestamp: datetime
    actions: list[NotificationAction]

def webpush_notification(endpoint: dict, content: Notification, **kwargs):
    if 'timestamp' in content:
        content['timestamp'] = content['timestamp'].timestamp()
    pywebpush.webpush(endpoint, json.dumps(content), 
                      vapid_private_key=settings.WEBPUSH['VAPID_PRIVATE_KEY'],
                      vapid_claims={'sub': 'mailto:' + settings.WEBPUSH['VAPID_ADMIN_EMAIL']},
                      **kwargs)
    
def update_achievements(request: HttpRequest, **kwargs):
    for achievement in Achievement.objects.exclude(pk__in=request.client.achievements.values_list('pk', flat=True)):
        if achievement.condition_fulfilled(client=request.client, **kwargs):
            request.client.achievements.add(achievement)
            messages.add_message(request, messages.SUCCESS, achievement.name, achievement.pk, fail_silently=True)