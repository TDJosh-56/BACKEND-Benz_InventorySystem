import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import OuterRef, Q, Subquery
from django.utils import timezone

from app_settings.models import Setting
from audit.services import log, Category
from production.models import ProductionRecord
from recipe.models import AutoArchiveState, Recipe

logger = logging.getLogger(__name__)
ARCHIVE_AFTER_DAYS = 30


def autoarchive():
    settings = Setting.objects.first()
    if not settings or not settings.autoarchiveoldrecipe:
        return None

    cutoff = timezone.now() - timedelta(days=ARCHIVE_AFTER_DAYS)
    last_used = (ProductionRecord.objects
                 .filter(recipe_name=OuterRef('name'))
                 .order_by('-timestamp')
                 .values('timestamp')[:1])

    stale = list(
        Recipe.objects.filter(is_archive=False)
        .annotate(last_used=Subquery(last_used))
        .filter(Q(last_used__lt=cutoff) | Q(last_used__isnull=True, created_at__lt=cutoff))
    )
    Recipe.objects.filter(pk__in=[r.pk for r in stale]).update(is_archive=True)
    for r in stale:
        log(Category.RECIPE, 'Recipe archived', r.name, 'Auto-archived', recipe=r)
    return len(stale)


def autoarchive_if_due():
    """Runs autoarchive() at most once per day. Never raises, so it can't break the recipe list."""
    try:
        today = timezone.localdate()
        with transaction.atomic():
            state, _ = AutoArchiveState.objects.select_for_update().get_or_create(pk=1)
            if state.last_run == today:
                return None
            state.last_run = today
            state.save(update_fields=['last_run'])
        return autoarchive()
    except Exception:
        logger.exception('Auto-archive failed')
        return None