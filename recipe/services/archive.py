
from datetime import timedelta

from django.db.models import OuterRef, Subquery
from django.utils import timezone

from audit.services import log, Category, Delta
from app_settings.models import Setting
from production.models import ProductionRecord
from recipe.models import Recipe


def autoarchive():
    settings = Setting.load()

    if not settings.autoarchiveoldrecipe:
        return 0

    cutoff_date = timezone.now() - timedelta(days=30)

    latest_production = (
        ProductionRecord.objects
        .filter(recipe_name__iexact=OuterRef('name'))
        .order_by('-timestamp')
        .values('timestamp')[:1]
    )

    recipes = (
        Recipe.objects
        .filter(is_archive=False)
        .annotate(last_used=Subquery(latest_production))
    )

    archived_count = 0

    for recipe in recipes:
        last_used = recipe.last_used or recipe.created_at

        if last_used and last_used < cutoff_date:
            recipe.is_archive = True
            recipe.save(update_fields=['is_archive'])

            log(
                Category.RECIPE,
                'Recipe automatically archived',
                recipe.name,
                'Archived',
                Delta.NEUTRAL,
            )

            archived_count += 1

    return archived_count
