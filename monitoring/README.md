# Système de Monitoring Lexa

## Vue d'ensemble

Ce module fournit un système complet de surveillance de la santé (health checks) pour l'application Lexa, incluant :
- Infrastructure (Redis, PostgreSQL, Celery)
- APIs externes (OpenAI, Stripe, Active Trail, Adobe)
- Services de traduction (LARA Bridge)
- Containers Docker

## Installation

Le module est déjà installé et configuré. Les migrations ont été appliquées.

## Utilisation

### 1. Interface Admin - Déclenchement Manuel

Connectez-vous à l'interface admin : https://test.portail.lexamt.fr/fr/admin/

Sur la page d'accueil, vous verrez une nouvelle section "System Health Monitoring" avec deux boutons :
- **🚀 Run Health Checks** : Lance tous les tests immédiatement
- **📊 View Results** : Consulte l'historique des résultats

### 2. Tests Actuellement Implémentés

#### ✅ Infrastructure
- **Redis** : Connectivité, opérations SET/GET, utilisation mémoire
- **PostgreSQL** : Connectivité, requêtes, taille de la base de données

#### 🔄 En cours d'implémentation
- Celery Workers
- OpenAI API
- Stripe API
- Active Trail API
- Adobe PDF Services
- LARA Bridge (traduction texte, document, glossaire)
- Docker containers (Lexa, LARA)

### 3. Exécution Quotidienne (Celery)

Les tests seront exécutés automatiquement chaque jour via Celery Beat (à configurer).

## Test Manuel - Redis & PostgreSQL

Pour tester le système actuellement :

1. Allez sur https://test.portail.lexamt.fr/fr/admin/
2. Cliquez sur "🚀 Run Health Checks" dans la section violette en haut
3. Confirmez l'exécution
4. Vérifiez les résultats :
   - Message de succès/erreur en haut
   - Liste détaillée dans "Health Check Results"
   - Résumé dans "Health Check Runs"

## Structure du Code

```
monitoring/
├── __init__.py
├── apps.py                 # Configuration Django
├── models.py               # Modèles (HealthCheckResult, HealthCheckRun)
├── admin.py                # Interface admin
├── runner.py               # Orchestrateur des tests
├── tasks.py                # Tâches Celery
├── checks/
│   ├── __init__.py
│   ├── base.py            # Classes de base
│   ├── infrastructure.py  # Tests Redis, PostgreSQL, Celery
│   ├── external_apis.py   # Tests OpenAI, Stripe, etc. (à venir)
│   ├── translation.py     # Tests LARA (à venir)
│   └── docker.py          # Tests Docker (à venir)
└── migrations/
```

## Prochaines Étapes

1. ✅ **Test 1** : Redis & PostgreSQL (ACTUEL - À TESTER)
2. Celery Workers
3. OpenAI API
4. Stripe API
5. Active Trail API
6. Adobe PDF Services
7. LARA Bridge - Traduction de texte
8. LARA Bridge - Traduction de document
9. LARA Bridge - Glossaire (création/suppression)
10. Docker containers

## Configuration Celery Beat (À faire)

Ajouter dans `legal/settings.py` :

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'run-daily-health-checks': {
        'task': 'monitoring.run_scheduled_health_checks',
        'schedule': crontab(hour=2, minute=0),  # 2h du matin chaque jour
    },
}
```

## Notes

- Chaque test est indépendant et ne bloque pas les autres
- Les résultats sont stockés en base de données pour historique
- Les temps d'exécution sont mesurés pour détecter les ralentissements
- Le code est modulaire et facile à étendre
