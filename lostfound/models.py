from typing import Any, Collection, Self
from django.db import models
from django.urls import reverse, NoReverseMatch

# Create your models here.
from .modelfield import BinaryFileField, File

class Tracker(models.Model):
    name = models.CharField(max_length=255)
    tag = models.CharField(max_length=8, unique=True)
    thumbnail: File = BinaryFileField(default=b'')

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

class TrackerUpdate(models.Model):
    tracker = models.ForeignKey(Tracker, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    altitude = models.DecimalField(max_digits=5, decimal_places=2, null=True, default=None)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2)
    altitude_accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, default=None)
    heading = models.DecimalField(max_digits=5, decimal_places=2, null=True, default=None)
    speed = models.DecimalField(max_digits=5, decimal_places=2, null=True, default=None)

    message = models.CharField(blank=True, default="")
    picture: File = BinaryFileField(null=True, default=None)

    @classmethod
    def from_db(cls: type[Self], db: str | None, field_names: Collection[str], values: Collection[Any]) -> Self:
        instance = super().from_db(db, field_names, values)

        if instance.picture is not models.DEFERRED:
            try:
                instance.picture.url = reverse('lostfound:trackerupdate_picture', kwargs={'tag': instance.tracker.tag, 'id': instance.id})
            except NoReverseMatch:
                pass
        return instance

