"""
backend/decorators.py
=====================
Role-based access control decorators.
Usage:
    @login_required
    @role_required('admin')
    def my_view(request): ...
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required  # re-export for convenience


def role_required(*roles):
    """
    Decorator that restricts a view to users whose profile.role is in `roles`.
    Redirects to /dashboard/ with an error message if the role doesn't match.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            try:
                user_role = request.user.profile.role
            except Exception:
                messages.error(request, "Your account has no role assigned. Contact admin.")
                return redirect('login')

            if user_role in roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, f"Access denied. This page is for: {', '.join(roles)}.")
            return redirect('dashboard')
        return _wrapped
    return decorator


def admin_required(view_func):
    """Shortcut: only admin role allowed."""
    return role_required('admin')(view_func)


def hod_required(view_func):
    """Shortcut: hod and admin allowed."""
    return role_required('hod', 'admin')(view_func)


def lecturer_required(view_func):
    """Shortcut: lecturer, hod, and admin allowed."""
    return role_required('lecturer', 'hod', 'admin')(view_func)


def student_required(view_func):
    """Shortcut: student role only."""
    return role_required('student')(view_func)
