from django.db import models
from django.core.exceptions import ValidationError

class Subcategory(models.Model):
    subcategory = models.CharField(max_lenght=20)

class Recipe(models.Model):
    name = models.CharField(max_length=50)
    category = models.CharField()
    yield_per_batch = models.IntegerField(max_lenght=20)
    yield_unit = models.CharField
    price = models.IntegerField()
    description = models.CharField(max_length=200)
    image = models.ImageField(upload_to='product/', validators=[validate_image_size])
    is_archive = models.BooleanField(default=False)
    ingredients = models.ManyToManyField('ingredient.Ingredient', blank=True)


def validate_image_size(file):
    max_mb = 5
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("Image must not exceed 5 MB")