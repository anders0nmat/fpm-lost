from typing import Any, Collection, Iterable, Optional, Self, Callable, Protocol
from django.db import models
from django.urls import reverse, NoReverseMatch
from django.contrib.sessions.models import Session
from django.utils import html
from django.utils.safestring import mark_safe
from django.core.validators import RegexValidator

# Create your models here.
from .modelfield import BinaryFileField, File, AutoLowerCharField

import logging

import urllib3

logger = logging.Logger('lostfound')

class Tracker(models.Model):
    tag = AutoLowerCharField(max_length=16, unique=True)
    name = models.CharField(max_length=255)
    thumbnail: File = BinaryFileField(default=b'')

    trackersubscription_set: models.QuerySet["TrackerSubscription"]
    trackerupdate_set: models.QuerySet["TrackerUpdate"]

    @classmethod
    def from_db(cls: type[Self], db: str | None, field_names: Collection[str], values: Collection[Any]) -> Self:
        instance = super().from_db(db, field_names, values)

        if instance.thumbnail is not models.DEFERRED:
            try:
                instance.thumbnail.url = reverse('lostfound:tracker_thumbnail', kwargs={
                    'tag': instance.tag
                })
            except NoReverseMatch:
                pass
        return instance
    
    def __str__(self) -> str:
        return self.name
    
def handler_list():
    return [(k, k) for k in Achievement._handlers.keys()]

class AchievementHandler(Protocol):
    def __call__(self, client: "Client", condition: Any, **kwargs: Any) -> tuple[int, int]: ...

class Achievement(models.Model):
    _handlers: dict[str, AchievementHandler] = {}

    name = models.CharField()
    description = models.CharField(blank=True, default="")
    badge: File = BinaryFileField(default=b'')

    visible = models.BooleanField(default=True)
    description_visible = models.BooleanField(default=True)
    progress_visible = models.BooleanField(default=True)

    condition_function = models.CharField(choices=handler_list)
    condition = models.JSONField()

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name
    
    def completion_rate(self) -> float:
        return 100 * self.client_set.count() / Client.objects.count()

    @classmethod
    def from_db(cls: type[Self], db: str | None, field_names: Collection[str], values: Collection[Any]) -> Self:
        instance = super().from_db(db, field_names, values)

        if instance.badge is not models.DEFERRED:
            try:
                instance.badge.url = reverse('lostfound:achievement_badge', kwargs={
                    'pk': instance.pk
                })
            except NoReverseMatch:
                pass
        return instance

    def condition_progress(self, client: "Client", **kwargs) -> tuple[int, int] | bool:
        try:
            condition_function = self._handlers[self.condition_function]

            return condition_function(client=client, condition=self.condition, **kwargs)
        except:
            pass
        return False
    
    def condition_fulfilled(self, client: "Client", **kwargs) -> bool:
        progress = self.condition_progress(client=client, **kwargs)
        if isinstance(progress, bool):
            return progress
        else:
            return progress[0] >= progress[1]

    @classmethod
    def handler(cls, name=None, func=None):
        def _handler(name, func):
            cls._handlers[name] = func
        if name is None and func is None:
            # @handler()
            def f(func: Callable):
                _handler(func.__name__, func)
                return func
            return f
        elif name is not None and func is None:
            if callable(name):
                # @handler
                _handler(name.__name__, name)
                return name
            else:
                # @handler('foo')
                # @handler('name='foo')
                def f(func):
                    _handler(name, func)
                    return func
                return f
        elif name is not None and func is not None:
            # @handler(name='foo', func=foo)
            _handler(name, func)
            return func
        else:
            raise NotImplementedError(f'Invalid arguments for decorator {cls}.handler: {name=}, {func=}')

class Client(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, primary_key=True)
    shadow_banned = models.BooleanField(default=False)
    achievements = models.ManyToManyField(Achievement, blank=True)
    trackers = models.ManyToManyField(Tracker, blank=True)

    # Reverse relation
    trackersubscription: "TrackerSubscription" | None
    trackerupdate_set: models.QuerySet["TrackerUpdate"]

    @property
    def is_privileged(self) -> bool:
        return hasattr(self, 'trackersubscription')

    def __str__(self) -> str:
        return self.trackersubscription.name if self.is_privileged else self.session.session_key

class TrackerUpdate(models.Model):
    class Meta:
        ordering = ['-timestamp']

    tracker = models.ForeignKey(Tracker, on_delete=models.CASCADE)
    creator = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.DecimalField(max_digits=9, decimal_places=2)
    altitude = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, default=None)
    altitude_accuracy = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, default=None)
    heading = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, default=None)
    speed = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, default=None)

    address = models.CharField(max_length=255, default="", editable=False)

    message = models.CharField(verbose_name='Nachricht', blank=True, default="")
    picture: File = BinaryFileField(verbose_name='Bild', null=True, default=None, blank=True)

    @property
    def speed_kmh(self):
        return self.speed / 3.6 if self.speed else None
    
    @property
    def address_html(self):
        return mark_safe(html.escape(self.address).replace('\n', '<br>'))
        
    @classmethod
    def from_db(cls: type[Self], db: str | None, field_names: Collection[str], values: Collection[Any]) -> Self:
        instance = super().from_db(db, field_names, values)

        if instance.picture is not models.DEFERRED and instance.picture is not None:
            try:
                instance.picture.url = reverse('lostfound:trackerupdate_picture', args=[instance.tracker.tag, instance.id])
            except NoReverseMatch:
                pass
        return instance

    def get_absolute_url(self):
        return reverse("lostfound:tracker_detail", args=[self.tracker.tag])
    
    def save(self, *args, **kwargs) -> None:
        if not self.address:
            try:
                response = urllib3.request("GET", f"https://nominatim.openstreetmap.org/reverse?lat={self.latitude}&lon={self.longitude}&format=json&addressdetails=1")

                if response.status == 200:
                    rsp = response.json()
                    d = rsp['address']
                    address = ''
                    if rsp['class'] != 'highway' and rsp['name']:
                        address += rsp['name'] + '\n'
                    address += d['road']
                    if 'house_number' in d:
                        address += ' ' + d['house_number']
                    address += ',\n'
                    address += d['postcode'] + ' ' + d['city']
                    self.address = address
            except Exception as ex:
                logger.info(f'Fetching address for {self} resulted in error', ex)
        
        return super().save(*args, **kwargs)

class TrackerSubscription(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=100)
    subscribed_to = models.ManyToManyField(Tracker, blank=True)
    subscription_details = models.JSONField(null=True, blank=True, default=None)

    def __str__(self) -> str:
        return self.name

