# Generated migration for adding default entities

from django.db import migrations


def add_default_entities(apps, schema_editor):
    """
    Add default entities to the Entity model if they don't already exist.
    """
    Entity = apps.get_model('domains', 'Entity')
    
    # List of default entities with their properties
    default_entities = [
        {
            'id': 1,
            'name': 'EURLEX - Doc des organes de l\'Europe',
            'png_file': 'entities/eur-lex-60-40-a.png'
        },
        {
            'id': 2,
            'name': 'ONU - Organisation des nations unies',
            'png_file': 'entities/onu-60-40-a.png'
        },
        {
            'id': 3,
            'name': 'GRECO - Groupe d\'état contre la Corruption',
            'png_file': 'entities/greco-60-40-a.png'
        },
        {
            'id': 4,
            'name': 'INTERPOL - Organisation internationale de police criminelle',
            'png_file': 'entities/interpol-60-40-a.png'
        },
        {
            'id': 5,
            'name': 'OIT - Organisation Internationale du Travail',
            'png_file': 'entities/oit-60-40-a.png'
        },
        {
            'id': 6,
            'name': 'OMC - Organisation Mondiale du Commerce',
            'png_file': 'entities/omc-60-40-a.png'
        },
        {
            'id': 7,
            'name': 'OHCHR - Haut-Commissariat aux droits de l\'homme',
            'png_file': 'entities/ohcr-60-40-a.png'
        },
        {
            'id': 9,
            'name': 'CCE- Cour des comptes Européenne',
            'png_file': 'entities/ecc-60-40-a_1DJkWBE.png'
        },
        {
            'id': 10,
            'name': 'COE - Conseil de l\'Europe',
            'png_file': 'entities/conseur-60-40-a.png'
        },
        {
            'id': 11,
            'name': 'WIPO - Office Européen de la Propriété Intellectuelle',
            'png_file': 'entities/wipo-60-40-a.jpg'
        },
        {
            'id': 12,
            'name': 'ECOSOC - Conseil économique des Nations Unies',
            'png_file': 'entities/ecosoc-60-40-a.png'
        },
        {
            'id': 13,
            'name': 'IATE - Interactive Terminology for Europe',
            'png_file': 'entities/iate-60-40-a.jpg'
        },
        {
            'id': 14,
            'name': 'FMI - fond Monétaire international',
            'png_file': 'entities/fmi-60-40-a.png'
        },
        {
            'id': 15,
            'name': 'BCE - Banque central d\'investissement',
            'png_file': 'entities/bce-60-40-a.jpg'
        },
        {
            'id': 16,
            'name': 'EUIPO - European union intellectual property organisation',
            'png_file': 'entities/euipo-60-40-a.png'
        },
        {
            'id': 17,
            'name': 'IMO - International maritime organization',
            'png_file': 'entities/imo-60-40-a.png'
        },
        {
            'id': 18,
            'name': 'CJUE - Cour de justice de l\'union européenne',
            'png_file': 'entities/cjue-60-40-a.png'
        },
    ]
    
    # Add each entity if it doesn't already exist
    for entity_data in default_entities:
        entity, created = Entity.objects.get_or_create(
            id=entity_data['id'],
            defaults={
                'name': entity_data['name'],
                'png_file': entity_data['png_file']
            }
        )
        if created:
            print(f"Created entity: {entity.name}")
        else:
            print(f"Entity already exists: {entity.name}")


def remove_default_entities(apps, schema_editor):
    """
    Remove default entities (reverse migration).
    """
    Entity = apps.get_model('domains', 'Entity')
    
    # List of entity IDs to remove during reverse migration
    entity_ids = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    
    # Delete entities with these IDs
    deleted_count = Entity.objects.filter(id__in=entity_ids).delete()[0]
    print(f"Deleted {deleted_count} default entities")


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0010_update_domain_group_icons'),
    ]

    operations = [
        migrations.RunPython(
            add_default_entities,
            remove_default_entities,
            elidable=True,
        ),
    ]
