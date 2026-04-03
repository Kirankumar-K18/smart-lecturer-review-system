"""
backend/utils.py
================
Shared utility functions used across views.
"""

from django.contrib.auth.models import User
from django.db import transaction

from .models import UserProfile, Student, Lecturer, HOD, ActivityLog


def get_client_ip(request):
    """Extract real client IP from request headers."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_activity(user, log_type, description, request=None, extra_data=None):
    """Create an ActivityLog entry. Safe to call from any view."""
    ActivityLog.objects.create(
        user        = user,
        log_type    = log_type,
        description = description,
        ip_address  = get_client_ip(request) if request else None,
        extra_data  = extra_data or {},
    )


@transaction.atomic
def create_user_with_role(
    username, email, password, role,
    first_name='', last_name='', department=None, phone=''
):
    """
    Create a Django User + UserProfile + role-specific profile in one transaction.
    Returns the created User object.
    Raises ValueError if username/email already exists.
    """
    if User.objects.filter(username=username).exists():
        raise ValueError(f"Username '{username}' is already taken.")
    if User.objects.filter(email=email).exists():
        raise ValueError(f"Email '{email}' is already registered.")
    if role == 'admin':
        raise ValueError("Cannot create admin via this function. Use create_admin command.")

    user = User.objects.create_user(
        username   = username,
        email      = email,
        password   = password,
        first_name = first_name,
        last_name  = last_name,
    )

    # UserProfile is auto-created by signal — update it
    profile = user.profile
    profile.role       = role
    profile.department = department
    profile.phone      = phone
    profile.save()

    # Create role-specific profile
    if role == 'student':
        Student.objects.create(
            user       = user,
            department = department,
        )
    elif role == 'lecturer':
        Lecturer.objects.create(
            user       = user,
            department = department,
        )
    elif role == 'hod':
        HOD.objects.create(
            user       = user,
            department = department,
        )

    return user


def get_dashboard_url(user):
    """Return the correct dashboard URL for a given user's role."""
    try:
        role = user.profile.role
    except Exception:
        return '/login/'

    mapping = {
        'admin':    '/admin-dashboard/',
        'hod':      '/hod-dashboard/',
        'lecturer': '/lecturer-dashboard/',
        'student':  '/student-dashboard/',
    }
    return mapping.get(role, '/dashboard/')


def get_attendance_summary(student):
    """
    Returns a dict of {subject: {total, present, absent, late, percentage}}
    for a given Student instance.
    """
    from .models import Subject
    summary = {}
    for subject in student.subjects.all():
        records = student.attendance_records.filter(subject=subject)
        total   = records.count()
        present = records.filter(status='present').count()
        absent  = records.filter(status='absent').count()
        late    = records.filter(status='late').count()
        pct     = round(present / total * 100, 1) if total else 0.0

        summary[subject.code] = {
            'subject_name': subject.name,
            'total':        total,
            'present':      present,
            'absent':       absent,
            'late':         late,
            'percentage':   pct,
            'status':       'Eligible' if pct >= 75 else ('Warning' if pct >= 60 else 'Critical'),
        }
    return summary
