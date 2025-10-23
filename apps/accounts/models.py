from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .managers import UserManager

class User(AbstractUser):
    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_('Required. Must be a valid email address.')
    )
    
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text=_('User profile picture')
    )
    
    bio = models.TextField(
        _('biography'),
        max_length=500,
        blank=True,
        help_text=_('Short biography about the user')
    )
    
    email_verified = models.BooleanField(
        _('email verified'),
        default=False,
        help_text=_('Designates whether the user has verified their email address.')
    )
    
    created_at = models.DateTimeField(
        _('date joined'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('last updated'),
        auto_now=True
    )
    
    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self) -> str:
        return self.username
    
    def get_absolute_url(self) -> str:
        return reverse('accounts:profile', kwargs={'username': self.username})
    
    def get_full_name(self) -> str:
        full_name = super().get_full_name()
        return full_name if full_name else self.username
    
    def get_ratings_count(self) -> int:
        return self.ratings.count()
    
    def get_comments_count(self) -> int:
        return self.comments.count()


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_tokens',
        verbose_name=_('user')
    )
    
    token = models.CharField(
        _('token'),
        max_length=255,
        unique=True,
        db_index=True
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    expires_at = models.DateTimeField(
        _('expires at')
    )
    
    is_used = models.BooleanField(
        _('is used'),
        default=False
    )
    
    class Meta:
        verbose_name = _('email verification token')
        verbose_name_plural = _('email verification tokens')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self) -> str:
        return f"Token for {self.user.username}"
    
    def is_expired(self) -> bool:
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def mark_as_used(self) -> None:
        self.is_used = True
        self.save(update_fields=['is_used'])


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        verbose_name=_('user')
    )
    
    token = models.CharField(
        _('token'),
        max_length=255,
        unique=True,
        db_index=True
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    expires_at = models.DateTimeField(
        _('expires at')
    )
    
    is_used = models.BooleanField(
        _('is used'),
        default=False
    )
    
    class Meta:
        verbose_name = _('password reset token')
        verbose_name_plural = _('password reset tokens')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self) -> str:
        return f"Password reset token for {self.user.username}"
    
    def is_expired(self) -> bool:
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def mark_as_used(self) -> None:
        self.is_used = True
        self.save(update_fields=['is_used'])