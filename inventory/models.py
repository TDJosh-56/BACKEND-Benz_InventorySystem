from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from .units import UNITS, convert

UNIT_CHOICES = [(u, u) for u in UNITS]


class Ingredient(models.Model):
    CATEGORY_CHOICES = [('Ingredient', 'Ingredient'), ('Material', 'Material')]

    name = models.CharField(max_length=100)
    current_stock = models.DecimalField(
        max_digits=14, decimal_places=4, default=0,
        validators=[MinValueValidator(0)])
    reorder_threshold = models.DecimalField(
        max_digits=14, decimal_places=4, default=0,
        validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    reorder_unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    cost_item = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default='Ingredient')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                condition=models.Q(is_active=True),
                name='unique_active_ingredient_name',
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.current_stock} {self.unit})'

    @property
    def threshold_in_stock_unit(self):
        converted = convert(self.reorder_threshold, self.reorder_unit, self.unit)
        return self.reorder_threshold if converted is None else converted

    @property
    def status(self):
        if self.current_stock <= 0:
            return 'Out of Stock'
        if self.current_stock <= self.threshold_in_stock_unit:
            return 'Low Stock'
        return 'In Stock'


class InventoryTransaction(models.Model):
    class Type(models.TextChoices):
        INITIAL = 'initial', 'Initial stock'
        ADDITION = 'addition', 'Addition'
        DEDUCTION = 'deduction', 'Deduction'
        ADJUSTMENT = 'adjustment', 'Adjustment'
        PRODUCTION = 'production', 'Production'

    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=Type.choices)
    quantity_change = models.DecimalField(max_digits=14, decimal_places=4)  # signed
    previous_stock = models.DecimalField(max_digits=14, decimal_places=4)
    new_stock = models.DecimalField(max_digits=14, decimal_places=4)
    reference = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [models.Index(fields=['ingredient', 'created_at'])]

    def __str__(self):
        return f'{self.ingredient_id} {self.transaction_type} {self.quantity_change}'