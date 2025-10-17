from django.db import migrations

DOMAIN_GROUPS_ICONS = [
    ("Tax law", "percent"),
    ("Corporate", "buildings"),
    ("Criminal law", "gavel"),
    ("Litigation", "scales"),
    ("IP/IT", "lightbulb"),
    ("Maritime law", "anchor"),
    ("Real-estate", "house"),
    ("Public law", "bank"),
    ("Business law", "briefcase"),
    ("Finance law", "currency-dollar"),
    ("Social law", "users"),
    ("Other", "dots-three"),
]

def update_domain_group_icons(apps, schema_editor):
    DomainGroup = apps.get_model("domains", "DomainGroup")
    for name, icon in DOMAIN_GROUPS_ICONS:
        try:
            group = DomainGroup.objects.get(name=name)
            group.icon = icon
            group.save()
        except DomainGroup.DoesNotExist:
            pass

class Migration(migrations.Migration):
    dependencies = [
        ("domains", "0009_auto_20250730_1536"),
    ]
    operations = [
        migrations.RunPython(update_domain_group_icons),
    ]
