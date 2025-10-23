# apps/movies/signals.py
from django.db.models.signals import pre_delete
from django.dispatch import receiver
import os

from .models import Movie


@receiver(pre_delete, sender=Movie)
def movie_pre_delete(sender, instance, **kwargs):
    # Delete poster file if it exists
    if instance.poster:
        if os.path.isfile(instance.poster.path):
            os.remove(instance.poster.path)

    # Delete video file if it exists
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
