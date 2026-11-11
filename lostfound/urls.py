from django.urls import path

from . import views

app_name = 'lostfound'
urlpatterns = [
    path('', views.RedirectView.as_view(pattern_name='lostfound:tracker_list', permanent=True)),

    path('trackers/', views.tracker_list, name="tracker_list"),
    path('trackers/<str:tag>/', views.TrackerDetail.as_view(), name="tracker_detail"),
    path('trackers/<str:tag>/found/', views.TrackerFoundView.as_view(), name="tracker_found"),
    path('trackers/<str:tag>/thumbnail/', views.tracker_thumbnail, name="tracker_thumbnail"),
    path('trackers/<str:tag>/<int:id>/picture/', views.trackerupdate_picture, name="trackerupdate_picture"),
    path('settings/', views.settings_view, name='settings'),
    path('sw.js', views.TemplateView.as_view(content_type="application/javascript", template_name="lostfound/sw.js")),
    path('achievements/', views.achievements, name="achievements"),
    path('achievements/<int:pk>/badge', views.achievement_badge, name="achievement_badge")
]
