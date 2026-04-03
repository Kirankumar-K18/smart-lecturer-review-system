"""
backend/management/commands/create_admin.py
===========================================
Creates the sole admin superuser for Smart Lecturer Review System.

Usage:
    python manage.py create_admin
    python manage.py create_admin --username admin --email you@gmail.com --password secret
    python manage.py create_admin --force     ← update password if already exists
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from backend.models import UserProfile


class Command(BaseCommand):
    help = "Create the primary admin (superuser) for Smart Lecturer Review System."

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin',
                            help='Admin username (default: admin)')
        parser.add_argument('--email', type=str, default='kiran19.7.06.l@gmail.com',
                            help='Admin email')
        parser.add_argument('--password', type=str, default='admin123',
                            help='Admin password (default: admin123)')
        parser.add_argument('--force', action='store_true',
                            help='Update password/email if admin already exists')

    def handle(self, *args, **options):
        username = options['username']
        email    = options['email']
        password = options['password']
        force    = options['force']

        existing = User.objects.filter(profile__role='admin').first()

        if existing and not force:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️  Admin already exists: '{existing.username}'\n"
                f"   Use --force to update credentials.\n"
            ))
            return

        with transaction.atomic():
            if existing and force:
                existing.set_password(password)
                existing.email        = email
                existing.is_staff     = True
                existing.is_superuser = True
                existing.save()
                profile, _ = UserProfile.objects.get_or_create(user=existing)
                profile.role             = 'admin'
                profile.is_primary_admin = False
                profile.save()
                self.stdout.write(self.style.SUCCESS(
                    f"\n✅ Admin credentials updated!\n"
                    f"   Username : {existing.username}\n"
                    f"   Email    : {email}\n"
                    f"   Password : {password}\n"
                ))
                return

            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.ERROR(
                    f"\n❌ Username '{username}' is already taken.\n"
                    f"   Choose a different --username or use --force.\n"
                ))
                return

            user = User.objects.create_superuser(
                username=username, email=email, password=password
            )
            # Signal creates UserProfile automatically — just update role
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role             = 'admin'
            profile.is_primary_admin = False
            profile.save()

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Admin superuser created!\n"
            f"\n   ┌──────────────────────────────────────────┐\n"
            f"   │  Username : {username:<29}│\n"
            f"   │  Email    : {email:<29}│\n"
            f"   │  Password : {password:<29}│\n"
            f"   └──────────────────────────────────────────┘\n"
            f"\n   Django Admin  →  http://localhost:8000/admin/\n"
            f"   App Login     →  http://localhost:8000/login/\n"
            f"\n   ⚠️  Change the password before deploying!\n"
        ))
