from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import TrackerUpdate, Achievement, Client
from .utils import webpush_notification, pywebpush, update_achievements
from http import HTTPStatus

import logging

logger = logging.Logger('lostfound')

@receiver(post_save, sender=TrackerUpdate)
async def tracker_update(sender, instance: TrackerUpdate, created, **_):
    if not created:
        return
    
    tracker = instance.tracker
    async for subscriber in tracker.trackersubscription_set.all():
        if subscriber.subscription_details:
            try:
                kwargs = {}
                if instance.message:
                    kwargs.update(body=instance.message)
                if instance.picture:
                    kwargs.update(image=instance.picture.url)
                webpush_notification(subscriber.subscription_details, {
                    'title': f'{tracker.name} wurde gefunden',
                    'navigate': reverse('lostfound:tracker_detail', args=[tracker.tag]),
                    'icon': reverse('lostfound:tracker_thumbnail', kwargs={'tag': tracker.tag}),
                    'lang': 'de',
                    'body': instance.address,
                } | kwargs)
            except Exception as ex:
                if ex is pywebpush.WebPushException and ex.status_code == HTTPStatus.GONE:
                    logger.warn(f'Push subscription "{tracker.name}" is gone', ex)
                else:
                    logger.warn(f'Pushing to "{tracker.name}" resulted in error', ex)

@receiver(post_save, sender=Achievement)
def refresh_achievements(sender, instance: Achievement, created, **_):
    if not created:
        return
    
    for client in Client.objects.all():
        if instance.condition_fulfilled(client):
            client.achievements.add(instance)
            # Unfortunately no message because no request instance :(
        

