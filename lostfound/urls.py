from django.urls import path

from . import views

app_name = 'lostfound'
urlpatterns = [
    path("", views.IndexView.as_view()),

    path('trackers/'),
    path('trackers/<str:tag>/', name="tracker_detail"),
    path('trackers/<str:tag>/<int:id>', name="trackerupdate_detail"),
    path('trackers/<str:tag>/<int:id>/picture', name="trackerupdate_picture"),
    path('trackers/<str:tag>/thumbnail', views.tracker_thumbnail, name="tracker_thumbnail"),
    path('trackers/<str:tag>/found', name="tracker_found"),
]
