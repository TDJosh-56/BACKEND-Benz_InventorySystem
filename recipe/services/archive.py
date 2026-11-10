from datetime import timedelta

from django.utils import timezone
from django.db.models import Max

from app_settings.models import Setting
from production.models import ProductionRecord
from recipe.models import Recipe


def autoarchive():
    settings = Setting.objects.first()

    if not settings or not settings.autoarchiveoldrecipe:
        return

    one_month_ago = timezone.now() - timedelta(days=30)

    recipes = Recipe.objects.filter(is_archive=False).annotate(
        last_used=Max('production_records__created_at')
    )

    archived_count = 0

    for recipe in recipes:
        last_used = recipe.last_used or recipe.created_at

        if last_used and last_used < one_month_ago:
            recipe.is_archive = True
            recipe.save(update_fields=['is_archive'])
            archived_count += 1

    return archived_count