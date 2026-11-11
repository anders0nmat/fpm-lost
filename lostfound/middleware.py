
from django.http import HttpRequest
from django.core.exceptions import ImproperlyConfigured
from .models import Client
from django.contrib.sessions.models import Session

class SessionClientMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if not hasattr(request, 'session'):
            raise ImproperlyConfigured('SessionClientMiddleware requires session middleware')
        
        session = request.session
        if not session.get('_has_client', False):
            session['_has_client'] = True
            session.save()
                
        request.client, _ = Client.objects.get_or_create(session_id=session.session_key)

        response = self.get_response(request)

        return response
        