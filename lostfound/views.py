from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.http import HttpRequest, FileResponse

from .models import Tracker
# Create your views here.
class IndexView(TemplateView):
    template_name = 'lostfound/index.html'


def tracker_thumbnail(request: HttpRequest, tag: str):
    tracker = get_object_or_404(Tracker, tag=tag)
    return FileResponse(tracker.thumbnail, as_attachment=False, filename=tracker.name)
