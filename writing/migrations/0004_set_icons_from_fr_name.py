from django.db import migrations


def set_icons_from_fr_name(apps, schema_editor):
    Prompt = apps.get_model('writing', 'Prompt')
    PromptTranslation = apps.get_model('writing', 'PromptTranslation')

    # Build a mapping from French name to existing icon
    fr_translations = PromptTranslation.objects.filter(language='fr').select_related('prompt')
    name_to_icon = {}
    for translation in fr_translations:
        prompt = translation.prompt
        if getattr(prompt, 'icon', None):
            name = (translation.name or '').strip()
            if name and name not in name_to_icon:
                name_to_icon[name] = prompt.icon

    # Explicit fallback mapping to ensure key FR names have an icon
    explicit_fallback = {
        'Modification du genre': 'gender-neuter',
        'Style - formel': 'briefcase',
        'Anonymisation - Noms': 'detective',
        'Anonymisation - Chiffres': 'hash',
        'Résumé': 'list-magnifying-glass',
    }
    # Do not override existing mapping discovered from DB
    for fr_name, icon in explicit_fallback.items():
        if fr_name not in name_to_icon:
            name_to_icon[fr_name] = icon

    # Apply icon to prompts missing icon, based on their FR name
    updated_count = 0
    for translation in fr_translations:
        prompt = translation.prompt
        if not getattr(prompt, 'icon', None):
            name = (translation.name or '').strip()
            icon = name_to_icon.get(name)
            if icon:
                prompt.icon = icon
                prompt.save(update_fields=['icon'])
                updated_count += 1

    print(f"Updated {updated_count} prompts icons from FR names")


def noop_reverse(apps, schema_editor):
    # No-op reverse; we do not remove icons once set
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('writing', '0003_auto_20251015_1600'),
    ]
#test
    operations = [
        migrations.RunPython(set_icons_from_fr_name, noop_reverse, elidable=True),

    ]


