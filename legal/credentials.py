from .keys import MS_KEY, MMT_KEY
languages = [
    {
        'name': 'English',
        'name_fr': 'Anglais',
        'language': 'en',
        'pairs': [
            {
                'language': 'fr',
                'name': 'French',
                'name_fr': 'Français'
            }
        ]
    },
    {
        'name': 'French',
        'name_fr': 'Français',
        'language': 'fr',
        'pairs': [
            {
                'language': 'en',
                'name': 'English',
                'name_fr': 'Anglais'
            }
        ]
    }
]

provider_models = {
    'Microsoft': {
        'ms_en_fr_des': {
            'title': 'Droit des Sociétés',
            'title_fr': 'Droit des Sociétés',
            'provider': 'ms',
            'category_id': '4aaaeeba-cf81-4c57-8d82-ab5cec9aa4ca-LAW',
            'key': MS_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'ms_fr_en_des': {
            'title': 'Droit des Sociétés',
            'title_fr': 'Droit des Sociétés',
            'provider': 'ms',
            'category_id': '4aaaeeba-cf81-4c57-8d82-ab5cec9aa4ca-LAW',
            'key': MS_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'
        },
        'ms_en_fr_immobilier': {
            'title': 'Droit Immobilier',
            'title_fr': 'Droit Immobilier',
            'provider': 'ms',
            'category_id': '3823a279-8776-4b21-a7ed-c0d6d83379b3-LAW',
            'key': MS_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'ms_en_fr_social': {
            'title': 'Droit social',
            'title_fr': 'Droit social',
            'provider': 'ms',
            'category_id': '67bd74ac-cd32-4455-8749-efe8c9ce6698-LAW',
            'key': MS_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'ms_fr_en_social': {
            'title': 'Droit social',
            'title_fr': 'Droit social',
            'provider': 'ms',
            'category_id': '67bd74ac-cd32-4455-8749-efe8c9ce6698-LAW',
            'key': MS_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'
        },
        'ms_en_fr_financier': {
            'title': 'Droit financier',
            'title_fr': 'Droit financier',
            'provider': 'ms',
            'category_id': '1f67a0ef-c4d0-425c-a2d4-2c83f0213ce6-LAW',
            'key': MS_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'ms_fr_en_financier': {
            'title': 'Droit financier',
            'title_fr': 'Droit financier',
            'provider': 'ms',
            'category_id': '1f67a0ef-c4d0-425c-a2d4-2c83f0213ce6-LAW',
            'key': MS_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'
        },
        'ms_en_fr_commercial': {
            'title': 'Droit commercial',
            'title_fr': 'Droit commercial',
            'provider': 'ms',
            'category_id': '3749e601-f2e4-4c58-aee5-40ab57cfea3d-LAW',
            'key': MS_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'ms_fr_en_commercial': {
            'title': 'Droit commercial',
            'title_fr': 'Droit commercial',
            'provider': 'ms',
            'category_id': '3749e601-f2e4-4c58-aee5-40ab57cfea3d-LAW',
            'key': MS_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'
        },
        'ms_en_fr_litiges': {
            'title': 'Litiges',
            'title_fr': 'Litiges',
            'provider': 'ms',
            'category_id': 'c8e195f8-55ca-407d-906d-b52201cd219d-LAW',
            'key': MS_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'ms_fr_en_litiges': {
            'title': 'Litiges',
            'title_fr': 'Litiges',
            'provider': 'ms',
            'category_id': '4aaaeeba-cf81-4c57-8d82-ab5cec9aa4ca-LAW',
            'key': MS_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'
        }
    },
    'ModernMT': {
        'mmt_en_fr_des': {
            'title': 'Droit des sociétés',
            'title_fr': 'Droit des sociétés',
            'provider': 'mmt',
            'category_id': '325817',
            'key': MMT_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'mmt_fr_en_des': {
            'title': 'Droit des sociétés',
            'title_fr': 'Droit des sociétés',
            'provider': 'mmt',
            'category_id': '325817',
            'key': MMT_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'
        },
        'mmt_en_fr_commercial': {
            'title': 'Droit commercial',
            'title_fr': 'Droit commercial',
            'provider': 'mmt',
            'category_id': '325638',
            'key': MMT_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'mmt_fr_en_commercial': {
            'title': 'Droit commercial',
            'title_fr': 'Droit commercial',
            'provider': 'mmt',
            'category_id': '325638',
            'key': MMT_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'
        },
        'mmt_en_fr_social': {
            'title': 'Droit social',
            'title_fr': 'Droit social',
            'provider': 'mmt',
            'category_id': '328505',
            'key': MMT_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'mmt_fr_en_social': {
            'title': 'Droit social',
            'title_fr': 'Droit social',
            'provider': 'mmt',
            'category_id': '328505',
            'key': MMT_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'

        },
        'mmt_en_fr_financier': {
            'title': 'Droit financier',
            'title_fr': 'Droit financier',
            'provider': 'mmt',
            'category_id': '326013',
            'key': MMT_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'mmt_fr_en_financier': {
            'title': 'Droit financier',
            'title_fr': 'Droit financier',
            'provider': 'mmt',
            'category_id': '326013',
            'key': MMT_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'

        },
        'mmt_en_fr_fiscalité': {
            'title': 'Droit de la fiscalité',
            'title_fr': 'Droit de la fiscalité',
            'provider': 'mmt',
            'category_id': '326075',
            'key': MMT_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'mmt_fr_en_fiscalité': {
            'title': 'Droit de la fiscalité',
            'title_fr': 'Droit de la fiscalité',
            'provider': 'mmt',
            'category_id': '326075',
            'key': MMT_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'

        },
        'mmt_en_fr_immobilier': {
            'title': 'Droit immobilier',
            'title_fr': 'Droit immobilier',
            'provider': 'mmt',
            'category_id': '328309',
            'key': MMT_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'mmt_fr_en_immobilier': {
            'title': 'Droit immobilier',
            'title_fr': 'Droit immobilier',
            'provider': 'mmt',
            'category_id': '328309',
            'key': MMT_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'

        },
        'mmt_en_fr_litiges': {
            'title': 'Litiges',
            'title_fr': 'Litiges',
            'provider': 'mmt',
            'category_id': '328379',
            'key': MMT_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'mmt_fr_en_litiges': {
            'title': 'Litiges',
            'title_fr': 'Litiges',
            'provider': 'mmt',
            'category_id': '328379',
            'key': MMT_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'

        },
        'mmt_en_fr_pi_it': {
            'title': 'PI-IT',
            'title_fr': 'PI-IT',
            'provider': 'mmt',
            'category_id': '328806',
            'key': MMT_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'mmt_fr_en_pi_it': {
            'title': 'PI-IT',
            'title_fr': 'PI-IT',
            'provider': 'mmt',
            'category_id': '328806',
            'key': MMT_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'

        },
        'mmt_en_fr_finance': {
            'title': 'FINANCE',
            'title_fr': 'FINANCE',
            'provider': 'mmt',
            'category_id': '329012',
            'key': MMT_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'mmt_fr_en_finance': {
            'title': 'FINANCE',
            'title_fr': 'FINANCE',
            'provider': 'mmt',
            'category_id': '329012',
            'key': MMT_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'
        },
        'mmt_en_fr_brevets': {
            'title': 'BREVETS',
            'title_fr': 'BREVETS',
            'provider': 'mmt',
            'category_id': '329071',
            'key': MMT_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'mmt_fr_en_brevets': {
            'title': 'BREVETS',
            'title_fr': 'BREVETS',
            'provider': 'mmt',
            'category_id': '329071',
            'key': MMT_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'
        },
        'mmt_en_fr_generique': {
            'title': 'GENERIQUE',
            'title_fr': 'GENERIQUE',
            'provider': 'mmt',
            'category_id': '95966',
            'key': MMT_KEY,
            'source_lng': 'en',
            'target_lng': 'fr'
        },
        'mmt_fr_en_generique': {
            'title': 'GENERIQUE',
            'title_fr': 'GENERIQUE',
            'provider': 'mmt',
            'category_id': '95966',
            'key': MMT_KEY,
            'source_lng': 'fr',
            'target_lng': 'en'
        },

    }

}

# ca8b415515464c2c96fb8fee04682adf
