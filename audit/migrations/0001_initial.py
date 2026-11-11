import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('production', ''),
        ('inventory', ''),
        ('recipe', ''),
    ]