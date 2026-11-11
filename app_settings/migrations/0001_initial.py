from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('autoarchiveoldrecipe', models.BooleanField(default=True)),
                ('allow_production_override', models.BooleanField(default=True)),
                ('passcode_hash', models.CharField(blank=True, max_length=128)),

                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Setting',
            },
        ),
    ]
