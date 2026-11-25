from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_settings', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='setting',
            name='allow_production_override',
        ),
    ]
