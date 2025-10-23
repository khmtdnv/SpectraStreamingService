# apps/player/urls.py

from django.urls import path
from . import views

app_name = 'player'

urlpatterns = [
    # Video player
    path('watch/<slug:slug>/', views.VideoPlayerView.as_view(), name='watch'),

    # Video streaming
    path('stream/<slug:slug>/', views.StreamVideoView.as_view(), name='stream'),

    # Progress tracking
    path('save-progress/', views.save_progress, name='save_progress'),

    # Watch history
    path('history/', views.WatchHistoryListView.as_view(), name='history'),
    path('continue-watching/', views.continue_watching, name='continue_watching'),
]
