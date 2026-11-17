import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app_settings', '0001_initial'),
        ('inventory', '0002_ingredient_cost_item'),
        ('production', '0001_initial'),
        ('recipe', '0002_recipe_created_at_alter_recipe_image'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('category', models.CharField(
                    choices=[('inventory', 'Inventory'), ('production', 'Production'),
                             ('recipe', 'Recipe'), ('settings', 'Settings')],
                    max_length=20)),
                ('title', models.CharField(max_length=120)),
                ('subtitle', models.CharField(blank=True, max_length=255)),
                ('change_label', models.CharField(blank=True, max_length=120)),
                ('delta_type', models.CharField(
                    choices=[('positive', 'Positive'), ('negative', 'Negative'), ('neutral', 'Neutral')],
                    default='neutral', max_length=10)),
                ('ingredient', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to='inventory.ingredient')),
                ('production', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to='production.productionrecord')),
                ('recipe', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to='recipe.recipe')),
                ('settings', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to='app_settings.setting')),
            ],
            options={
                'ordering': ['-timestamp', '-id'],
                'indexes': [models.Index(fields=['category', 'timestamp'], name='audit_cat_ts_idx')],
            },
        ),
    ]
