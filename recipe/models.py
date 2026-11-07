from django.db import models


class Recipe(models.Model):
    name = models.CharField(max_length=50)
    category = models.IntegerField()
    subcategory = models.IntegerField()
    yield_per_batch = models.CharField(max_lenght=20)
    yield_unit = models.CharField
    price = models.IntegerField()
    description = models.CharField(max_length=200)
    image = models.ImageField(upload_to='product/')
    is_archive = models.BooleanField(default=False)
    ingredients = models.ManyToManyField('ingredient.Ingredient', blank=True)