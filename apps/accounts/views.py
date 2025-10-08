from typing import Any, Dict

from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetConfirmView
)
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, UpdateView, DetailView

from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    UserProfileUpdateForm
)
from .models import EmailVerificationToken, PasswordResetToken
from .tasks import send_verification_email, send_password_reset_email

User = get_user_model()


class UserRegistrationView(CreateView):
    """
    View for user registration.
    
    Handles user registration and sends email verification
    asynchronously using Celery.
    """
    
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:registration_complete')
    
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Redirect authenticated users to home page."""
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form: UserRegistrationForm) -> HttpResponse:
        """Save user and send verification email."""
        user = form.save()
        
        # Send verification email asynchronously
        send_verification_email.delay(user.id)
        
        messages.success(
            self.request,
            _('Registration successful! Please check your email to verify your account.')
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form: UserRegistrationForm) -> HttpResponse:
        """Handle invalid form submission."""
        messages.error(
            self.request,
            _('Please correct the errors below.')
        )
        return super().form_invalid(form)


class UserLoginView(LoginView):
    """
    View for user login.
    
    Supports login with username or email and 'remember me' functionality.
    """
    
    form_class = UserLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form: UserLoginForm) -> HttpResponse:
        """Handle successful login with 'remember me' functionality."""
        remember_me = form.cleaned_data.get('remember_me')
        
        if not remember_me:
            # Set session to expire when browser closes
            self.request.session.set_expiry(0)
        else:
            # Set session to expire in 2 weeks
            self.request.session.set_expiry(1209600)  # 2 weeks in seconds
        
        return super().form_valid(form)
    
    def form_invalid(self, form: UserLoginForm) -> HttpResponse:
        """Handle invalid login attempt."""
        messages.error(
            self.request,
            _('Invalid username/email or password.')
        )
        return super().form_invalid(form)


class UserLogoutView(LogoutView):
    """View for user logout."""
    
    next_page = reverse_lazy('accounts:login')
    
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Add logout message."""
        if request.user.is_authenticated:
            messages.info(request, _('You have been logged out successfully.'))
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordResetView(PasswordResetView):
    """
    Custom password reset view.
    
    Sends password reset email asynchronously using Celery.
    """
    
    form_class = CustomPasswordResetForm
    template_name = 'accounts/password_reset.html'
    success_url = reverse_lazy('accounts:password_reset_done')
    email_template_name = 'accounts/emails/password_reset_email.html'
    subject_template_name = 'accounts/emails/password_reset_subject.txt'
    
    def form_valid(self, form: CustomPasswordResetForm) -> HttpResponse:
        """Send password reset email asynchronously."""
        email = form.cleaned_data['email']
        user = User.objects.get(email=email)
        
        # Send password reset email asynchronously
        send_password_reset_email.delay(user.id)
        
        messages.success(self.request,
            _('Password reset link has been sent to your email.')
        )
        
        return redirect(self.success_url)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Custom password reset confirm view.
    
    Allows users to set a new password using the token from email.
    """
    
    form_class = CustomSetPasswordForm
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    
    def form_valid(self, form: CustomSetPasswordForm) -> HttpResponse:
        """Handle successful password reset."""
        messages.success(
            self.request,
            _('Your password has been reset successfully. You can now login with your new password.')
        )
        return super().form_valid(form)


class UserProfileView(DetailView):
    """
    View for displaying user profile.
    
    Shows public profile information including statistics.
    """
    
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        user = self.object
        
        context['ratings_count'] = user.get_ratings_count()
        context['comments_count'] = user.get_comments_count()
        
        # Get recent ratings (will be implemented when ratings app is ready)
        # context['recent_ratings'] = user.ratings.select_related('movie')[:5]
        
        return context


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for updating user profile.
    
    Allows users to update their profile information.
    """
    
    model = User
    form_class = UserProfileUpdateForm
    template_name = 'accounts/profile_update.html'
    
    def get_object(self, queryset=None) -> User:
        """Return the current user."""
        return self.request.user
    
    def get_success_url(self) -> str:
        """Redirect to user's profile after successful update."""
        return reverse_lazy('accounts:profile', kwargs={'username': self.request.user.username})
    
    def form_valid(self, form: UserProfileUpdateForm) -> HttpResponse:
        """Handle successful profile update."""
        messages.success(
            self.request,
            _('Your profile has been updated successfully.')
        )
        return super().form_valid(form)
    
    def form_invalid(self, form: UserProfileUpdateForm) -> HttpResponse:
        """Handle invalid form submission."""
        messages.error(
            self.request,
            _('Please correct the errors below.')
        )
        return super().form_invalid(form)


def verify_email(request: HttpRequest, token: str) -> HttpResponse:
    """
    View for email verification.
    
    Verifies user email using the token sent via email.
    
    Args:
        request: HTTP request object
        token: Email verification token from URL
        
    Returns:
        HttpResponse redirecting to appropriate page
    """
    try:
        verification_token = EmailVerificationToken.objects.select_related('user').get(
            token=token,
            is_used=False
        )
        
        if verification_token.is_expired():
            messages.error(
                request,
                _('This verification link has expired. Please request a new one.')
            )
            return redirect('accounts:resend_verification')
        
        # Verify the user's email
        user = verification_token.user
        user.email_verified = True
        user.save(update_fields=['email_verified'])
        
        # Mark token as used
        verification_token.mark_as_used()
        
        messages.success(
            request,
            _('Your email has been verified successfully! You can now login.')
        )
        
        return redirect('accounts:login')
        
    except EmailVerificationToken.DoesNotExist:
        messages.error(
            request,
            _('Invalid verification link.')
        )
        return redirect('accounts:login')


@login_required
def resend_verification_email(request: HttpRequest) -> HttpResponse:
    """
    View for resending verification email.
    
    Allows users to request a new verification email.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse with appropriate message
    """
    user = request.user
    
    if user.email_verified:
        messages.info(
            request,
            _('Your email is already verified.')
        )
        return redirect('accounts:profile', username=user.username)
    
    # Send new verification email
    send_verification_email.delay(user.id)
    
    messages.success(
        request,
        _('A new verification email has been sent to your email address.')
    )
    
    return redirect('accounts:profile', username=user.username)


def registration_complete(request: HttpRequest) -> HttpResponse:
    """
    View for registration complete page.
    
    Shows a message after successful registration.
    """
    return render(request, 'accounts/registration_complete.html')


def password_reset_done(request: HttpRequest) -> HttpResponse:
    """
    View for password reset done page.
    
    Shows a message after password reset email has been sent.
    """
    return render(request, 'accounts/password_reset_done.html')


def password_reset_complete(request: HttpRequest) -> HttpResponse:
    """
    View for password reset complete page.
    
    Shows a message after password has been reset successfully.
    """
    return render(request, 'accounts/password_reset_complete.html')