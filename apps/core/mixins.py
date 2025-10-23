from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy


class EmailVerificationRequiredMixin:
    verification_url = reverse_lazy('accounts:resend_verification')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.email_verified:
            messages.warning(
                request,
                'Please verify your email address to access this page.'
            )
            return redirect(self.verification_url)
        return super().dispatch(request, *args, **kwargs)


class AjaxResponseMixin:
    def is_ajax(self):
        return (
            self.request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            self.request.headers.get('HX-Request') == 'true'
        )