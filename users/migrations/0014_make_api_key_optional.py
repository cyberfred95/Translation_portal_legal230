# Generated manually for making api_key optional

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_user_language'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usergroup',
            name='api_key',
            field=models.CharField(
                blank=True, 
                help_text='If not provided, will be automatically generated', 
                max_length=256, 
                null=True
            ),
        ),
    ]
