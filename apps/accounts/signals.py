from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import os

User = get_user_model()


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    if created:
        pass


@receiver(pre_delete, sender=User)
def user_pre_delete(sender, instance, **kwargs):
    if instance.avatar:
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)