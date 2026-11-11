from django.contrib import admin
from django import forms

from . import models
from .modelfield import BinaryFileField

class AdminFileWidget(forms.ClearableFileInput):
    template_name = "admin/widgets/clearable_file_input.html"

# Register your models here.

class TrackerUpdateInline(admin.TabularInline):
    model = models.TrackerUpdate
    extra = 0

    exclude = [
        'latitude', 'longitude', 'accuracy',
        'altitude', 'altitude_accuracy',
        'speed', 'heading',
        'picture', 'message',
    ]
    readonly_fields = ['tracker', 'creator', 'timestamp', 'address', 'short_message', 'has_picture']

    @admin.display
    def short_message(self, instance: models.TrackerUpdate):
        return instance.message[:32]
    
    @admin.display(boolean=True)
    def has_picture(self, instance: models.TrackerUpdate):
        return instance.picture is not None

@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'tracker_count', 'update_count', 'achievement_count', 'shadow_banned']

    filter_horizontal = ['achievements', 'trackers']
    inlines = [TrackerUpdateInline]

    @admin.display
    def update_count(self, instance: models.Client):
        return instance.trackerupdate_set.count()
    
    @admin.display
    def achievement_count(self, instance: models.Client):
        return instance.achievements.count()
    
    @admin.display
    def tracker_count(self, instance: models.Client):
        return instance.trackers.count()

class TrackerUpdateForm(forms.ModelForm):
    class Meta:
        model = models.TrackerUpdate
        fields = '__all__'
        widgets = {
            'message': forms.Textarea(),
        }

@admin.register(models.TrackerUpdate)
class TrackerUpdateAdmin(admin.ModelAdmin):
    form = TrackerUpdateForm
    readonly_fields = ['address']
    list_display = ['tracker', 'timestamp', 'address', 'short_message', 'has_picture']

    list_filter = ['tracker']

    @admin.display
    def short_message(self, instance: models.TrackerUpdate):
        return instance.message[:32]
    
    @admin.display(boolean=True)
    def has_picture(self, instance: models.TrackerUpdate):
        return instance.picture is not None

@admin.register(models.Tracker)
class TrackerAdmin(admin.ModelAdmin):
    formfield_overrides={
        BinaryFileField: {'widget': AdminFileWidget},
    }
    inlines=[TrackerUpdateInline]

    list_display = ['name', 'update_count']

    @admin.display
    def update_count(self, instance: models.Tracker):
        return instance.trackerupdate_set.count()


admin.site.register(models.TrackerSubscription)
admin.site.register(models.Achievement, list_display=['name', 'visible', 'completion_rate'], formfield_overrides={
    BinaryFileField: {'widget': AdminFileWidget},
})
