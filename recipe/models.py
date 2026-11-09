from django.db import models
from django.core.exceptions import ValidationError


def validate_image_size(file):
    max_mb = 5
    if file.size > max_mb * 1024 * 1024:
        raise ValidationError("Image must not exceed 5 MB")
    
class Subcategory(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name

class Recipe(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food'),
        ('drinks', 'Drinks')
    ]
    name = models.CharField(max_length=50)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='recipes')
    yield_per_batch = models.IntegerField()
    yield_unit = models.CharField(max_length=20)
    price = models.FloatField()
    description = models.CharField(max_length=200)
    image = models.ImageField(upload_to='product/', validators=[validate_image_size])
    is_archive = models.BooleanField(default=False)
    ingredients = models.ManyToManyField('ingredient.Ingredient', through='RecipeIngredient', blank=True)

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients')
    ingredient = models.ForeignKey('ingredient.Ingredient', on_delete=models.CASCADE)
    quantity = models.FloatField()
    unit = models.CharField(max_length=10)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'], name='unique_recipe_ingredient')
        ]
