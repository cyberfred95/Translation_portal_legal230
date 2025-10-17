# Generated migration for adding default domain-entity relationships

from django.db import migrations


def add_default_domain_entities(apps, schema_editor):
    """
    Add default domain-entity relationships if they don't already exist.
    """
    Domain = apps.get_model('domains', 'Domain')
    Entity = apps.get_model('domains', 'Entity')
    
    # List of default domain-entity relationships (domain_name, entity_name)
    default_relationships = [
        ("Competition", "IATE - Interactive Terminology for Europe"),  # id 1: domain 65, entity 13
        ("Contracts", "IATE - Interactive Terminology for Europe"),    # id 2: domain 66, entity 13
        ("Customs", "IATE - Interactive Terminology for Europe"),      # id 3: domain 67, entity 13
        ("HR", "OIT - Organisation Internationale du Travail"),        # id 4: domain 60, entity 5
        ("Labour law", "OIT - Organisation Internationale du Travail"), # id 5: domain 61, entity 5
        ("Social benefits", "OIT - Organisation Internationale du Travail"), # id 6: domain 58, entity 5
        ("Social security", "OIT - Organisation Internationale du Travail"), # id 7: domain 59, entity 5
        ("Banking", "FMI - fond Monétaire international"),             # id 8: domain 64, entity 14
        ("Banking", "BCE - Banque central d'investissement"),          # id 9: domain 64, entity 15
        ("Insurance", "FMI - fond Monétaire international"),           # id 10: domain 63, entity 14
        ("Insurance", "BCE - Banque central d'investissement"),        # id 11: domain 63, entity 15
        ("Investment", "FMI - fond Monétaire international"),          # id 12: domain 62, entity 14
        ("Investment", "BCE - Banque central d'investissement"),       # id 13: domain 62, entity 15
        ("Accounting", "CCE- Cour des comptes Européenne"),            # id 14: domain 76, entity 9
        ("Tax", "CCE- Cour des comptes Européenne"),                   # id 15: domain 75, entity 9
        ("GDPR", "EUIPO - European union intellectual property organisation"), # id 16: domain 71, entity 16
        ("Industrial designs", "EUIPO - European union intellectual property organisation"), # id 17: domain 84, entity 16
        ("Patents", "EUIPO - European union intellectual property organisation"), # id 18: domain 70, entity 16
        ("Crimes/proceedings", "CJUE - Cour de justice de l'union européenne"), # id 19: domain 87, entity 18
        ("Crimes/proceedings", "ONU - Organisation des nations unies"), # id 20: domain 87, entity 2
        ("Criminal finance", "CJUE - Cour de justice de l'union européenne"), # id 21: domain 69, entity 18
        ("Criminal finance", "ONU - Organisation des nations unies"),   # id 22: domain 69, entity 2
        ("Arbitration", "CJUE - Cour de justice de l'union européenne"), # id 23: domain 91, entity 18
        ("Arbitration", "IATE - Interactive Terminology for Europe"),   # id 24: domain 91, entity 13
        ("Litigation", "CJUE - Cour de justice de l'union européenne"), # id 25: domain 79, entity 18
        ("Litigation", "IATE - Interactive Terminology for Europe"),    # id 26: domain 79, entity 13
        ("Maritime law", "IMO - International maritime organization"),  # id 27: domain 77, entity 17
        ("Real Estate", "IATE - Interactive Terminology for Europe"),   # id 28: domain 74, entity 13
        ("Town planning", "IATE - Interactive Terminology for Europe"), # id 29: domain 86, entity 13
        ("Climate", "IATE - Interactive Terminology for Europe"),       # id 30: domain 90, entity 13
        ("Transport", "IATE - Interactive Terminology for Europe"),     # id 31: domain 89, entity 13
        ("Corporate", "IATE - Interactive Terminology for Europe"),     # id 32: domain 80, entity 13
    ]
    
    added_count = 0
    skipped_count = 0
    
    # Add each relationship if both domain and entity exist and relationship doesn't already exist
    for domain_name, entity_name in default_relationships:
        try:
            domain = Domain.objects.get(name=domain_name)
            entity = Entity.objects.get(name=entity_name)
            
            # Check if relationship already exists
            if not domain.entities.filter(name=entity_name).exists():
                domain.entities.add(entity)
                added_count += 1
                print(f"Added relationship: Domain '{domain.name}' -> Entity '{entity.name}'")
            else:
                skipped_count += 1
                print(f"Relationship already exists: Domain '{domain.name}' -> Entity '{entity.name}'")
                
        except Domain.DoesNotExist:
            print(f"Warning: Domain with name '{domain_name}' does not exist, skipping relationship")
            skipped_count += 1
        except Entity.DoesNotExist:
            print(f"Warning: Entity with name '{entity_name}' does not exist, skipping relationship")
            skipped_count += 1
    
    print(f"Migration completed: {added_count} relationships added, {skipped_count} skipped")


def remove_default_domain_entities(apps, schema_editor):
    """
    Remove default domain-entity relationships (reverse migration).
    """
    Domain = apps.get_model('domains', 'Domain')
    Entity = apps.get_model('domains', 'Entity')
    
    # List of relationships to remove (domain_name, entity_name)
    relationships_to_remove = [
        ("Competition", "IATE - Interactive Terminology for Europe"),
        ("Contracts", "IATE - Interactive Terminology for Europe"),
        ("Customs", "IATE - Interactive Terminology for Europe"),
        ("HR", "OIT - Organisation Internationale du Travail"),
        ("Labour law", "OIT - Organisation Internationale du Travail"),
        ("Social benefits", "OIT - Organisation Internationale du Travail"),
        ("Social security", "OIT - Organisation Internationale du Travail"),
        ("Banking", "FMI - fond Monétaire international"),
        ("Banking", "BCE - Banque central d'investissement"),
        ("Insurance", "FMI - fond Monétaire international"),
        ("Insurance", "BCE - Banque central d'investissement"),
        ("Investment", "FMI - fond Monétaire international"),
        ("Investment", "BCE - Banque central d'investissement"),
        ("Accounting", "CCE- Cour des comptes Européenne"),
        ("Tax", "CCE- Cour des comptes Européenne"),
        ("GDPR", "EUIPO - European union intellectual property organisation"),
        ("Industrial designs", "EUIPO - European union intellectual property organisation"),
        ("Patents", "EUIPO - European union intellectual property organisation"),
        ("Crimes/proceedings", "CJUE - Cour de justice de l'union européenne"),
        ("Crimes/proceedings", "ONU - Organisation des nations unies"),
        ("Criminal finance", "CJUE - Cour de justice de l'union européenne"),
        ("Criminal finance", "ONU - Organisation des nations unies"),
        ("Arbitration", "CJUE - Cour de justice de l'union européenne"),
        ("Arbitration", "IATE - Interactive Terminology for Europe"),
        ("Litigation", "CJUE - Cour de justice de l'union européenne"),
        ("Litigation", "IATE - Interactive Terminology for Europe"),
        ("Maritime law", "IMO - International maritime organization"),
        ("Real Estate", "IATE - Interactive Terminology for Europe"),
        ("Town planning", "IATE - Interactive Terminology for Europe"),
        ("Climate", "IATE - Interactive Terminology for Europe"),
        ("Transport", "IATE - Interactive Terminology for Europe"),
        ("Corporate", "IATE - Interactive Terminology for Europe"),
    ]
    
    removed_count = 0
    
    # Remove each relationship if it exists
    for domain_name, entity_name in relationships_to_remove:
        try:
            domain = Domain.objects.get(name=domain_name)
            entity = Entity.objects.get(name=entity_name)
            
            if domain.entities.filter(name=entity_name).exists():
                domain.entities.remove(entity)
                removed_count += 1
                print(f"Removed relationship: Domain '{domain.name}' -> Entity '{entity.name}'")
                
        except (Domain.DoesNotExist, Entity.DoesNotExist):
            # Silently skip if domain or entity doesn't exist
            pass
    
    print(f"Reverse migration completed: {removed_count} relationships removed")


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0011_add_default_entities'),
    ]

    operations = [
        migrations.RunPython(
            add_default_domain_entities,
            remove_default_domain_entities,
            elidable=True,
        ),
    ]
