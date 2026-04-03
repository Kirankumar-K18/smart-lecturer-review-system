"""
backend/management/commands/seed_bad_words.py
=============================================
Seeds a default list of blocked/inappropriate words into the BadWord table.

Usage:
    python manage.py seed_bad_words
    python manage.py seed_bad_words --clear   (wipe existing before seeding)
"""

from django.core.management.base import BaseCommand
from backend.models import BadWord

DEFAULT_BAD_WORDS = [
    "idiot", "stupid", "dumb", "fool", "moron", "loser",
    "hate", "terrible", "useless", "worthless", "pathetic",
    "awful", "rubbish", "trash", "garbage", "disgusting",
    "incompetent", "worst", "horrible", "disgrace",
]


class Command(BaseCommand):
    help = "Seed default bad/blocked words into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing bad words before seeding.'
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = BadWord.objects.count()
            BadWord.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {count} existing bad word(s)."))

        created = 0
        skipped = 0
        for word in DEFAULT_BAD_WORDS:
            _, was_created = BadWord.objects.get_or_create(word=word.lower().strip())
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Bad words seeded: {created} added, {skipped} already existed.\n"
        ))
