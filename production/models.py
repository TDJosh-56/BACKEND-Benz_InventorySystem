from django.db import models
from django.utils import timezone

class ProductionRecord(models.Model):
    #expects string name
    recipe_name = models.CharField(max_length = 255)
    quantity = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now)

    #edit log tracking (required by frontend)
    comment = models.TextField(blank=True, null=True)
    edited_at = models.DateTimeField(blank=True, null=True)
    original_quantity = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Production #{self.id} - {self.recipe_name} ({self.quantity})"
