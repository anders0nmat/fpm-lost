from typing import Any, Dict
from django.forms.models import BaseModelForm
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, CreateView, RedirectView
from django.views.generic.edit import ModelFormMixin
from django.http import HttpRequest, FileResponse, HttpResponse, Http404
from django.conf import settings
from django import forms, http
from django.db.models import Value
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.urls import reverse

from .models import Tracker, TrackerUpdate, Client, Achievement
from .forms import TrackerUpdateForm, TrackerFoundForm
from .utils import update_achievements

class HttpRequest(HttpRequest):
    client: Client

# Create your views here.

@never_cache
def tracker_list(request: HttpRequest):
    if request.method == 'POST':
        form = TrackerFoundForm(request.POST, label_suffix='')
        if form.is_valid():
            return redirect('lostfound:tracker_found', tag=form.cleaned_data['tracker'].tag)
        
        update_achievements(request, form_value=form.data.get('tracker'))
    else:
        form = TrackerFoundForm(label_suffix='')

    context = {
        'form': form,
        'tracker_count': Tracker.objects.count(),
        'tracker_list': Tracker.objects.all() if request.client.is_privileged else request.client.trackers.all(),
        'has_settings': request.client.is_privileged,
    }

    return render(request, 'lostfound/tracker_list.html', context)

class TrackerDetail(DetailView):
    model = Tracker
    slug_field = slug_url_kwarg = 'tag'

@method_decorator(never_cache, name="dispatch")
class TrackerFoundView(CreateView):
    model = TrackerUpdate
    form_class = TrackerUpdateForm

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        self.tracker = get_object_or_404(Tracker, tag=self.kwargs['tag'])

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        return super().get_context_data(**kwargs) | { 'tracker': self.tracker }
    
    def get_initial(self) -> Dict[str, Any]:
        return {'tracker': self.tracker, 'creator': self.request.client}

    def get_form_kwargs(self) -> Dict[str, Any]:
        return super().get_form_kwargs() | { 'label_suffix': '' }
    
    def get_success_url(self) -> str:
        return reverse('lostfound:tracker_detail', args=[self.tracker.tag])

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        client: Client = self.request.client
        client.trackers.add(form.cleaned_data['tracker'])
        
        if client.shadow_banned:
            # Skip model save
            form.save = lambda: None

        response = super().form_valid(form)

        update_achievements(self.request)

        return response
    
    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        coord_errors = {}
        errors = (form.errors.as_data().get(field, []) for field in ('latitude', 'longitude', 'accuracy'))
        errors = ({e.code: e for e in l} for l in errors)
        for error_dict in errors:
            coord_errors.update(error_dict)

        for error in coord_errors.values():
            form.add_error('location', error)
        return super().form_invalid(form)

class SubscriptionForm(forms.Form):
    webpush_subscription = forms.JSONField(label='PushAPI Key', widget=forms.TextInput(attrs={'readonly': ''}), initial={})
    subscribed_trackers = forms.ModelMultipleChoiceField(Tracker.objects.all(), label="Abonnierte Tracker", widget=forms.CheckboxSelectMultiple)

def settings_view(request: HttpRequest):
    if not request.client.is_privileged:
        raise Http404()
    subscriber = request.client.trackersubscription
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, label_suffix='')
        if form.is_valid():
            subscriber.subscription_details = form.cleaned_data['webpush_subscription']
            subscriber.subscribed_to.set(form.cleaned_data['subscribed_trackers'])
            subscriber.save()
            return redirect('lostfound:tracker_list')
    else:
        form = SubscriptionForm(initial={
                'subscribed_trackers': subscriber.subscribed_to.all(),
                'webpush_subscription': subscriber.subscription_details,
            },
            label_suffix='')

    context = {
        'form': form,
        'vapid_public_key': settings.WEBPUSH['VAPID_PUBLIC_KEY'],
    }
    return render(request, 'lostfound/settings.html', context)

def achievements(request: HttpRequest):
    locked_achievements = Achievement.objects.filter(visible=True).exclude(pk__in=request.client.achievements.values_list('pk', flat=True)).order_by('name').annotate(locked=Value(True))

    locked_achievements = list(locked_achievements)
    for a in locked_achievements:
        a.progress = a.condition_progress(request.client)

    return render(request, 'lostfound/achievements.html', {
        'unlocked_achievements': request.client.achievements.order_by('name'),
        'locked_achievements': locked_achievements,
        'total_count': Achievement.objects.count(),
        'hidden_count': Achievement.objects.filter(visible=False).exclude(pk__in=request.client.achievements.values_list('pk', flat=True)).count(),
    })

def tracker_thumbnail(request: HttpRequest, tag: str):
    tracker = get_object_or_404(Tracker, tag=tag)
    return FileResponse(tracker.thumbnail, as_attachment=False, filename=tracker.name, content_type="image/png")

def trackerupdate_picture(request: HttpRequest, tag: str, id: int):
    trackerupdate = get_object_or_404(TrackerUpdate, id=id)
    return FileResponse(trackerupdate.picture, as_attachment=False, content_type="image/*")

def achievement_badge(request: HttpRequest, pk: str):
    achievement = get_object_or_404(Achievement, pk=pk)
    return FileResponse(achievement.badge, as_attachment=False, filename=achievement.name, content_type="image/*")

