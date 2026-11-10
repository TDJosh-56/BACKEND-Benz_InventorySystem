from django.core.management.base import BaseCommand
from recipe.services.archive import autoarchive


class Command(BaseCommand):
    help = "Automatically archive unused recipes"

    def handle(self, *args, **options):
        count = autoarchive()

        self.stdout.write(
            self.style.SUCCESS(
                f"Archived {count} unused recipes."
            )
        )