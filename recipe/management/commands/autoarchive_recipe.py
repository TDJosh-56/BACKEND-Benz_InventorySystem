from django.core.management.base import BaseCommand
from recipe.services.archive import autoarchive


class Command(BaseCommand):
    help = "Archive recipes that have not been used for 30 days"

    def handle(self, *args, **options):
        count = autoarchive()

        if count is None:
            self.stdout.write(self.style.WARNING("Auto-archive is turned off in settings."))
            return

        self.stdout.write(self.style.SUCCESS(f"Archived {count} unused recipe(s)."))