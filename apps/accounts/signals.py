from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import os

User = get_user_model()


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for post-save User model.
    
    Performs actions after a user is created or updated.
    
    Args:
        sender: The model class (User)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Perform actions for newly created users
        # For example, create related models or send welcome email
        pass


@receiver(pre_delete, sender=User)
def user_pre_delete(sender, instance, **kwargs):
    """
    Signal handler for pre-delete User model.
    
    Cleans up user avatar file when user is deleted.
    
    Args:
        sender: The model class (User)
        instance: The actual instance being deleted
        **kwargs: Additional keyword arguments
    """
    # Delete avatar file if it exists
    if instance.avatar:
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)