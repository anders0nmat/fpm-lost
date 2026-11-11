
from django.forms import ModelForm, Textarea, HiddenInput
from django import forms
from django.db import models

from .models import TrackerUpdate, Tracker
from .modelfield import RoundingDecimalField, DummyField

def rounded_decimal_fields(field, **kwargs):
    if isinstance(field, models.DecimalField):
        return field.formfield(form_class=RoundingDecimalField, **kwargs)
    return field.formfield(**kwargs)

class TrackerUpdateForm(ModelForm):
    class Meta:
        model = TrackerUpdate
        fields = '__all__'
        widgets = {
            'tracker': HiddenInput(),
            'creator': HiddenInput(),
            'message': Textarea(attrs={'placeholder': ' ', 'cols': '', 'rows': '3'}),

            'latitude': HiddenInput(),
            'longitude': HiddenInput(),
            'altitude': HiddenInput(),
            'accuracy': HiddenInput(),
            'altitude_accuracy': HiddenInput(),
            'heading': HiddenInput(),
            'speed': HiddenInput(),
        }
        formfield_callback = rounded_decimal_fields
    location = DummyField()


class TrackerFoundForm(forms.Form):
    tracker = forms.ModelChoiceField(
        Tracker.objects.all(),
        to_field_name="tag",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': ' ', 'autocomplete': 'off', 'autocapitalize': 'off', 'spellcheck': 'false', 'autofill': 'off'}),
        error_messages={
            'invalid_choice': 'Den Tracker gibt es nicht.'
        })
    
    
