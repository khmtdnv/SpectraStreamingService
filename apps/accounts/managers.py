from django.contrib.auth.models import UserManager as BaseUserManager
from django.db.models import QuerySet


class UserManager(BaseUserManager):
    def create_user(self, username: str, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username: str, email: str, password: str = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

    def verified_users(self) -> QuerySet:
        return self.filter(email_verified=True, is_active=True)

    def active_users(self) -> QuerySet:
        return self.filter(is_active=True)