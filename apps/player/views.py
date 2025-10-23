# apps/player/views.py

"""
Views for player application.
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse, FileResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import ListView
import json

from apps.movies.models import Movie
from .models import WatchHistory


class VideoPlayerView(View):
    """
    View for displaying video player.
    """

    template_name = 'player/video_player.html'

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        """Display video player for a movie."""
        movie = get_object_or_404(
            Movie.objects.select_related('category'),
            slug=slug
        )

        # Get user's watch progress if authenticated
        watch_history = None
        if request.user.is_authenticated:
            watch_history = WatchHistory.objects.filter(
                user=request.user,
                movie=movie
            ).first()

        context = {
            'movie': movie,
            'watch_history': watch_history,
            'has_video': bool(movie.video_url or movie.video_file),
        }

        return render(request, self.template_name, context)


class StreamVideoView(View):
    """
    View for streaming video files with range support.
    """

    def get(self, request: HttpRequest, slug: str) -> FileResponse:
        """Stream video file with range support."""
        movie = get_object_or_404(Movie, slug=slug)

        if not movie.video_file:
            raise Http404("Video file not found")

        # Get the video file
        video_file = movie.video_file
        file_size = video_file.size

        # Handle range requests for seeking
        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_match = None

        if range_header:
            import re
            range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)

        if range_match:
            start = int(range_match.group(1))
            end = range_match.group(2)
            end = int(end) if end else file_size - 1
            length = end - start + 1

            video_file.open('rb')
            video_file.seek(start)
            data = video_file.read(length)
            video_file.close()

            response = HttpResponse(
                data,
                status=206,
                content_type='video/mp4'
            )
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response['Accept-Ranges'] = 'bytes'
            response['Content-Length'] = str(length)
        else:
            response = FileResponse(
                video_file.open('rb'),
                content_type='video/mp4'
            )
            response['Content-Length'] = str(file_size)
            response['Accept-Ranges'] = 'bytes'

        return response


@require_POST
@login_required
def save_progress(request: HttpRequest) -> JsonResponse:
    """
    Save user's video playback progress.
    """
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        progress = data.get('progress', 0)
        duration = data.get('duration', 0)

        movie = get_object_or_404(Movie, id=movie_id)

        # Update or create watch history
        watch_history, created = WatchHistory.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={
                'progress': int(progress),
                'duration': int(duration),
                'completed': progress >= duration * 0.9  # 90% watched = completed
            }
        )

        return JsonResponse({
            'success': True,
            'progress': watch_history.progress,
            'percentage': watch_history.get_progress_percentage()
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


class WatchHistoryListView(LoginRequiredMixin, ListView):
    """
    View for displaying user's watch history.
    """

    model = WatchHistory
    template_name = 'player/watch_history.html'
    context_object_name = 'history'
    paginate_by = 20

    def get_queryset(self):
        """Get watch history for current user."""
        return WatchHistory.objects.filter(
            user=self.request.user
        ).select_related('movie', 'movie__category').order_by('-last_watched')


@login_required
def continue_watching(request: HttpRequest) -> HttpResponse:
    """
    View for displaying continue watching section.
    """
    history = WatchHistory.objects.filter(
        user=request.user,
        completed=False,
        progress__gt=0
    ).select_related('movie', 'movie__category').order_by('-last_watched')[:6]

    return render(request, 'player/continue_watching.html', {
        'history': history
    })
