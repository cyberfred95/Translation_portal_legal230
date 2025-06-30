

def get_glossary_username(glossary) -> str:
    if not glossary.user and not glossary.group:
        return "admin"

    if glossary.user:
        return glossary.user.username
    if glossary.group:
        return glossary.group.name
