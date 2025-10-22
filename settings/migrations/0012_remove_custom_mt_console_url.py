# Generated manually to remove CUSTOM_MT_CONSOLE_URL field

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0011_remove_glossaries_url_field'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mainsettings',
            name='CUSTOM_MT_CONSOLE_URL',
        ),
    ]
