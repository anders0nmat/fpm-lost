from typing import Any
from django.db.models import BinaryField, CharField
from django.core.files.base import ContentFile, File
from django import forms
from decimal import Decimal

class BinaryFile(ContentFile):
    def __init__(self, content: bytes | str, url: str = None) -> None:
        super().__init__(content, url)
        self.url = url

    def __str__(self) -> str:
        return self.name or self.url or ''
 
class BinaryFileField(BinaryField):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault('editable', True)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if not self.editable:
            kwargs["editable"] = False
        else:
            del kwargs["editable"]
        return name, path, args, kwargs

    def get_prep_value(self, value):
        if isinstance(value, File):
            value.seek(0)
            value = value.read()
        return value
    
    def from_db_value(self, value, expression, connection):
        return BinaryFile(value) if value is not None else value
    
    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.FileField,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
    
class RoundingDecimalField(forms.DecimalField):
    def round(self, value: Decimal):
        if self.decimal_places is None:
            return value
        return round(value, self.decimal_places)

    def to_python(self, value: Any | None) -> Any | None:
        value = super().to_python(value)
        return self.round(value) if value is not None else None

class DummyWidget(forms.HiddenInput):
    @property
    def is_hidden(self) -> bool:
        return True
    
    def render(self, name, value, attrs=None, renderer=None):
        return ""

class DummyField(forms.Field):
    def __init__(self) -> None:
        super().__init__(required=False, widget=DummyWidget)

class AutoLowerCharField(CharField):
    def to_python(self, value: Any) -> Any:
        value = super().to_python(value)
        return value.strip().lower() if value is not None else value

class AutoUpperCharField(CharField):
    def to_python(self, value: Any) -> Any:
        value = super().to_python(value)
        return value.upper() if value is not None else value
