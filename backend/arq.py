"""
backend/arq.py
==============
Django signals — auto-creates UserProfile for every new User.
Connected in backend/apps.py → ready().
"""

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def auto_create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a UserProfile when a new User is saved.
    For superusers (created via createsuperuser), the role is set to 'admin'.
    For everyone else, it defaults to 'student' (will be updated by registration flow).
    """
    if created:
        if not UserProfile.objects.filter(user=instance).exists():
            role = 'admin' if instance.is_superuser else 'student'
            UserProfile.objects.create(user=instance, role=role)
