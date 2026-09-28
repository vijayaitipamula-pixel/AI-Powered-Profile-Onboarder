from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import Resolver404, resolve
from django.utils import timezone


class TemporaryPasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.must_change_password:
            expires = request.user.temporary_password_expires_at
            if not expires or expires <= timezone.now():
                logout(request)
                return redirect('password_reset')
            try:
                match = resolve(request.path_info)
            except Resolver404:
                return redirect('password_change')
            if match.url_name not in {'password_change', 'logout'}:
                return redirect('password_change')
        return self.get_response(request)
