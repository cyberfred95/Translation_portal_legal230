# Generated manually on 2025-08-22 for updating domain icons

from django.db import migrations


def update_domain_icons(apps, schema_editor):
    """
    Update existing domains with their corresponding icons.
    Only updates existing domains, does not create new ones.
    """
    Domain = apps.get_model('domains', 'Domain')
    
    # Mapping of domain names to their corresponding Phosphor icons
    domain_icon_mapping = {
        'Accounting': 'calculator',
        'Arbitration': 'scales',
        'Banking': 'bank',
        'Climate': 'leaf',
        'Competition': 'trophy',
        'Contracts': 'file-text',
        'Corporate': 'buildings',
        'Crimes/proceedings': 'gavel',
        'Criminal finance': 'detective',
        'Customs': 'airplane',
        'GDPR': 'shield-check',
        'Generic': 'scales',
        'HR': 'users',
        'Industrial designs': 'palette',
        'Insurance': 'umbrella',
        'Investment': 'bank',
        'Labour law': 'person',
        'Litigation': 'gavel',
        'Maritime law': 'anchor',
        'Patents': 'lightbulb',
        'Real Estate': 'house',
        'Social benefits': 'heart',
        'Social security': 'shield-check',
        'Tax': 'percent',
        'Town planning': 'buildings',
        'Transport': 'car',
    }
    
    # Update only existing domains
    for domain_name, icon_name in domain_icon_mapping.items():
        try:
            domain = Domain.objects.get(name=domain_name)
            domain.icon = icon_name
            domain.save()
            print(f"Updated domain '{domain_name}' with icon '{icon_name}'")
        except Domain.DoesNotExist:
            print(f"Domain '{domain_name}' does not exist, skipping...")
            continue


def reverse_update_domain_icons(apps, schema_editor):
    """
    Reverse operation: set all domain icons to None
    """
    Domain = apps.get_model('domains', 'Domain')
    Domain.objects.all().update(icon=None)


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0009_auto_20250730_1536'),
    ]

    operations = [
        migrations.RunPython(
            update_domain_icons,
            reverse_update_domain_icons,
        ),
    ]
