"""Single entry point other apps use to write to the audit trail."""
from .models import AuditLog

Category = AuditLog.Category
Delta = AuditLog.Delta


def log(category, title, subtitle='', change='', delta=Delta.NEUTRAL,
        recipe=None, ingredient=None):
    return AuditLog.objects.create(
        category=category,
        title=title[:120],
        subtitle=(subtitle or '')[:255],
        change_label=(change or '')[:120],
        delta_type=delta,
        production=production,
        recipe=recipe,
        ingredient=ingredient,
    )


def fmt_qty(value):
    """12.5000 -> '12.5', 3.0000 -> '3'."""
    text = f'{float(value):.4f}'.rstrip('0').rstrip('.')
    return text or '0'
