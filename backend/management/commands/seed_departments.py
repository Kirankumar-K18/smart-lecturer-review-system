"""
backend/management/commands/seed_departments.py
===============================================
Seeds default departments into the Department table.

Usage:
    python manage.py seed_departments
    python manage.py seed_departments --clear
"""

from django.core.management.base import BaseCommand
from backend.models import Department

DEFAULT_DEPARTMENTS = [
    {"name": "Computer Science",       "code": "CS"},
    {"name": "Electronics Engineering","code": "EC"},
    {"name": "Mechanical Engineering", "code": "ME"},
    {"name": "Civil Engineering",      "code": "CE"},
    {"name": "Mathematics",            "code": "MA"},
    {"name": "Physics",                "code": "PH"},
    {"name": "Chemistry",              "code": "CH"},
    {"name": "MBA",                    "code": "MBA"},
    {"name": "Information Technology", "code": "IT"},
    {"name": "Electrical Engineering", "code": "EE"},
]


class Command(BaseCommand):
    help = "Seed default departments into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing departments before seeding.'
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = Department.objects.count()
            Department.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {count} existing department(s)."))

        created = 0
        skipped = 0
        for dept in DEFAULT_DEPARTMENTS:
            _, was_created = Department.objects.get_or_create(
                code=dept['code'],
                defaults={'name': dept['name']}
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Departments seeded: {created} added, {skipped} already existed.\n"
        ))
        self.stdout.write("Departments in database:")
        for d in Department.objects.order_by('name'):
            self.stdout.write(f"  [{d.code}]  {d.name}")
        self.stdout.write("")
