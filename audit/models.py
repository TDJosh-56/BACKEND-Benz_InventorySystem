from django.db import models
from django.utils import timezone


class AuditLog(models.Model):

    class Category(models.TextChoices):
        INVENTORY = 'inventory', 'Inventory'
        PRODUCTION = 'production', 'Production'
        RECIPE = 'recipe', 'Recipe'
        SETTINGS = 'settings', 'Settings'

    class Delta(models.TextChoices):
        POSITIVE = 'positive', 'Positive'
        NEGATIVE = 'negative', 'Negative'
        NEUTRAL = 'neutral', 'Neutral'

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    title = models.CharField(max_length=120)
    subtitle = models.CharField(max_length=255, blank=True)
    change_label = models.CharField(max_length=120, blank=True)
    delta_type = models.CharField(max_length=10, choices=Delta.choices, default=Delta.NEUTRAL)


    recipe = models.ForeignKey(
        'recipe.Recipe', null=True, blank=True, on_delete=models.SET_NULL)
    ingredient = models.ForeignKey(
        'inventory.Ingredient', null=True, blank=True, on_delete=models.SET_NULL)
    production = models.ForeignKey(
        'production.ProductionRecord', null=True, blank=True, on_delete=models.SET_NULL)
    settings = models.ForeignKey(
        'app_settings.Setting', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-timestamp', '-id']
        indexes = [models.Index(fields=['category', 'timestamp'])]

    def __str__(self):
        return f'[{self.category}] {self.title} - {self.subtitle}'

    @property
    def badge_text(self):
        return self.category.upper()