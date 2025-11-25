# Implémentation du système de metered billing Stripe

## 📋 Résumé de l'implémentation

Ce document décrit l'implémentation complète du système de facturation metered pour les abonnements API, permettant de suivre l'utilisation quotidienne et de l'envoyer automatiquement à Stripe.

## ✅ Fonctionnalités implémentées

### 1. Modèle CountMetered
- **Fichier**: `subscriptions/models.py`
- **Champs ajoutés**:
  - `reported`: `DateField` (remplace `BooleanField`) - Date de report à Stripe
  - `stripe_usage_record_id`: `CharField` - ID de l'enregistrement Stripe créé
- **Contrainte**: Unicité `(user_subscription, date)` pour éviter les doublons
- **Méthodes**:
  - `get_today_count_metered()`: Récupère le compteur du jour (lève ValueError si doublons)
  - `ensure_api_count_metered()`: Crée automatiquement un compteur pour les abonnements API

### 2. Modèle UserSubscription - Modifications
- **Fichier**: `subscriptions/models.py`
- **Champ ajouté**: `stripe_subscription_item_id` - ID Stripe de l'item metered
- **Migration**: `0016_usersubscription_stripe_subscription_item_id.py`
- **Logique automatique**:
  - Création automatique d'un `CountMetered` lors de la création/modification d'une souscription API
  - Vérification à chaque `save()` pour garantir l'existence du compteur du jour

### 3. Service d'envoi quotidien vers Stripe
- **Fichier**: `subscriptions/services/metered_usage.py`
- **Classe**: `MeteredUsageReporter`
- **Fonctionnalités**:
  - Sélection du dernier `CountMetered` non reporté par souscription API
  - Envoi à Stripe via `stripe.UsageRecord.create()` avec:
    - `action="set"`
    - `quantity=daily_translated_symbols_count`
    - `timestamp=minuit UTC` du jour concerné
  - Mise à jour de `reported` et `stripe_usage_record_id`
  - Création automatique du compteur du jour suivant
- **Tâche Celery**: `report_daily_metered_usage()` planifiée à 00:05 UTC

### 4. Intégration dans les webhooks Stripe
- **Fichiers modifiés**:
  - `stripe_webhooks/tasks_handlers/getter/get_payload.py`: Ajout de `get_item_data_subscription_item_id()`
  - `stripe_webhooks/tasks_handlers/customer_subscription_handlers.py`: Extraction et stockage de `subscription_item_id`
  - `stripe_webhooks/tasks_handlers/setter/set_userSubscription.py`: Stockage de `stripe_subscription_item_id`
  - `stripe_webhooks/tasks_handlers/error/error_messages.py`: Ajout de `not_found_subscription_item_id`

### 5. Incrémentation des compteurs lors des traductions
- **Fichier**: `subscriptions/helpers.py`
- **Fonction**: `add_translations()`
- **Logique**:
  - Incrémente les compteurs globaux de `UserSubscription`
  - Pour les abonnements API, incrémente aussi les compteurs journaliers de `CountMetered`
  - Validation: vérifie que le compteur existe, n'est pas déjà reporté, et qu'il n'y a pas de doublons

### 6. Interface Admin
- **Fichier**: `subscriptions/admin.py`
- **Classe**: `CountMeteredAdmin`
- **Fonctionnalités**:
  - Affichage des compteurs metered dans l'admin Django
  - Filtres par date, statut de report, recherche par email/usage_record_id
  - Champs en lecture seule pour éviter les modifications manuelles

## 🔧 Configuration

### Celery Beat Schedule
- **Fichier**: `legal/settings.py` et `legal/celery.py`
- **Tâche**: `report_daily_metered_usage`
- **Horaire**: Tous les jours à 00:05 UTC

### Variables d'environnement requises
- `STRIPE_API_KEY`: Clé API Stripe pour créer les Usage Records

## 📝 Structure des données

### CountMetered
```python
- date: DateField
- user_subscription: ForeignKey(UserSubscription)
- reported: DateField (null=True)  # Date d'envoi à Stripe
- stripe_usage_record_id: CharField (null=True)  # ID Stripe
- daily_translated_symbols_count: IntegerField
- daily_translated_words_count: IntegerField
- daily_translated_files_count: IntegerField
```

### UserSubscription (nouveaux champs)
```python
- stripe_subscription_item_id: CharField (null=True)  # ID Stripe de l'item metered
```

## 🧪 Tests unitaires

Tous les tests passent (66 tests):
- `stripe_webhooks/tests/test_getters.py`: Test de `get_item_data_subscription_item_id()`
- `stripe_webhooks/tests/test_setters.py`: Test de création avec `stripe_subscription_item_id`
- `stripe_webhooks/tests/test_subscription_handlers.py`: Tests des handlers avec item_id

## 🔄 Flux de fonctionnement

1. **Création d'une souscription API**:
   - Webhook `customer.subscription.created` → extraction de `subscription_item_id`
   - Création de `UserSubscription` avec `stripe_subscription_item_id`
   - Création automatique d'un `CountMetered` pour aujourd'hui

2. **Utilisation quotidienne**:
   - Chaque traduction incrémente `CountMetered.daily_translated_symbols_count`
   - Le compteur est lié à la date du jour

3. **Envoi quotidien à Stripe** (00:05 UTC):
   - Sélection du dernier `CountMetered` non reporté par souscription
   - Création d'un `UsageRecord` Stripe avec le total de la journée
   - Mise à jour de `reported` et `stripe_usage_record_id`
   - Création automatique du `CountMetered` du jour suivant

## 📦 Produit Stripe concerné

- **Product ID**: `prod_TOPELuhp8luEEZ`
- **Type**: Metered billing
- **Métrique**: Nombre de caractères traduits (`daily_translated_symbols_count`)
- **Clé Stripe**: `API_NbCar_Standard`

## ⚠️ Points d'attention

1. **SubscriptionType requis**: Le produit `prod_TOPELuhp8luEEZ` doit exister dans `SubscriptionType` avec `product_type='API'`
2. **Subscription Item ID**: Doit être fourni dans les webhooks Stripe (extrait automatiquement)
3. **Timestamp Stripe**: Utilise minuit UTC pour la date d'utilisation
4. **Gestion d'erreurs**: Les erreurs lors de l'envoi sont loggées mais n'interrompent pas le traitement des autres souscriptions

## 🚀 Prochaines étapes possibles

- [ ] Script de simulation d'achat (à recréer si nécessaire)
- [ ] Monitoring des échecs d'envoi (alertes si > N jours sans report)
- [ ] Dashboard de visualisation des usages metered
- [ ] Tests d'intégration avec Stripe (mode test)

## 📚 Fichiers modifiés/créés

### Modèles
- `subscriptions/models.py`: CountMetered, UserSubscription

### Services
- `subscriptions/services/metered_usage.py`: Service d'envoi vers Stripe

### Tâches
- `subscriptions/tasks.py`: Tâche Celery quotidienne

### Helpers
- `subscriptions/helpers.py`: Incrémentation des compteurs

### Webhooks
- `stripe_webhooks/tasks_handlers/getter/get_payload.py`: Extraction item_id
- `stripe_webhooks/tasks_handlers/customer_subscription_handlers.py`: Handlers
- `stripe_webhooks/tasks_handlers/setter/set_userSubscription.py`: Création souscriptions
- `stripe_webhooks/tasks_handlers/error/error_messages.py`: Messages d'erreur

### Admin
- `subscriptions/admin.py`: Interface CountMeteredAdmin

### Migrations
- `subscriptions/migrations/0015_auto_20251124_1619.py`: Migration CountMetered
- `subscriptions/migrations/0016_usersubscription_stripe_subscription_item_id.py`: Migration item_id

### Tests
- `stripe_webhooks/tests/test_getters.py`
- `stripe_webhooks/tests/test_setters.py`
- `stripe_webhooks/tests/test_subscription_handlers.py`
- `stripe_webhooks/tests/settings.py`

### Configuration
- `legal/settings.py`: Celery Beat schedule
- `legal/celery.py`: Configuration Celery

## 🔍 Commandes utiles

```bash
# Appliquer les migrations
python3 manage.py migrate

# Lancer les tests
python3 manage.py test stripe_webhooks.tests

# Vérifier la tâche Celery
celery -A legal beat --loglevel=info

# Voir les CountMetered dans l'admin
# http://localhost:8000/admin/subscriptions/countmetered/
```

## 📞 Notes importantes

- Le système crée automatiquement un `CountMetered` pour chaque souscription API
- L'envoi à Stripe se fait quotidiennement à 00:05 UTC
- Les erreurs sont loggées mais n'arrêtent pas le traitement
- Un seul `CountMetered` par jour par souscription (contrainte d'unicité)

