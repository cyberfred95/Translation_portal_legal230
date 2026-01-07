# Rapport : Passe-droits accordés par `is_staff`

Ce document liste tous les endroits où le statut `is_staff=True` donne un passe-droit (bypass) des vérifications normales dans l'application.

## 🔴 1. Vérifications de permissions d'abonnement

### `subscriptions/permissions.py`

#### `check_user_subscription_permission()` - Ligne 203
```python
if user.is_staff:
    return (True, SubscriptionPermissionError.SUCCESS, _("Staff user has full access."))
```
**Bypass :** Toutes les vérifications de permissions d'abonnement
- Pas de vérification de groupe
- Pas de vérification d'abonnement
- Pas de vérification de statut
- Pas de vérification de dates
- Pas de vérification d'accès à l'écriture

**Impact :** ⚠️ **CRITIQUE** - Les staff peuvent utiliser toutes les fonctionnalités sans abonnement

---

### `subscriptions/helpers.py`

#### `translation_allowed()` - Ligne 111
```python
if request.user.is_staff:
    return (True, None, None)
```
**Bypass :** Toutes les vérifications de quotas de traduction
- Pas de vérification de quotas (fichiers, mots, symboles)
- Pas de limite d'utilisation
- Pas de comptage des traductions

**Impact :** ⚠️ **CRITIQUE** - Les staff peuvent traduire sans limite

---

## 🟠 2. Vérifications de permissions d'accès

### `legal/views/translate.py`

#### `default_glossary_allowed()` - Ligne 21
```python
if self.request.user.is_staff:
    return True
```
**Bypass :** Vérification d'accès aux glossaires officiels
- Accès aux glossaires officiels sans abonnement avec `access_to_official_glossaries`

**Impact :** ⚠️ **MOYEN** - Accès aux fonctionnalités premium

#### `post()` - Ligne 41
```python
if not request.user.is_staff and not request.user.group:
    return JsonResponse({"detail": "You have to be staff or to be in group"}, status=400)
```
**Bypass :** Vérification d'appartenance à un groupe
- Peut utiliser la page de traduction sans groupe

**Impact :** ⚠️ **MOYEN** - Accès à la traduction sans groupe

---

### `legal/views/my_team.py`

#### `test_func()` - Ligne 26
```python
if self.request.user.is_staff:
    return True
```
**Bypass :** Vérification d'admin de groupe
- Accès à la page "Mon équipe" sans être admin du groupe

**Impact :** ⚠️ **MOYEN** - Accès à la gestion d'équipe

#### `_get_user_queryset()` - Ligne 222
```python
if self.request.user.is_staff:
    return User.objects.all()
```
**Bypass :** Filtrage par groupe
- Voit tous les utilisateurs de l'application, pas seulement ceux de son groupe

**Impact :** ⚠️ **CRITIQUE** - Accès à tous les utilisateurs (confidentialité)

#### `check_premium_status()` - Ligne 180
```python
return user.is_staff or hasattr(user, 'subscription') and getattr(user.subscription, 'is_premium', False)
```
**Bypass :** Statut premium
- Considéré comme premium sans vérification d'abonnement

**Impact :** ⚠️ **MOYEN** - Affichage de fonctionnalités premium

#### `_can_edit_user()` - Ligne 275
```python
if current_user.is_staff:
    return True
```
**Bypass :** Restrictions d'édition d'utilisateur
- Peut éditer n'importe quel utilisateur

**Impact :** ⚠️ **CRITIQUE** - Peut modifier tous les utilisateurs

---

### `writing/views.py`

#### `WritingProcessAPIView.post()` - Ligne 63
```python
if not request.user.is_staff and not request.user.group:
    return Response(...)
```
**Bypass :** Vérification d'appartenance à un groupe
- Peut utiliser les fonctionnalités d'écriture sans groupe

**Impact :** ⚠️ **MOYEN** - Accès aux fonctionnalités d'écriture

---

### `users/views.py`

#### `UsersListView.get()` - Ligne 51
```python
if request.user.is_staff:
    return Response(GroupSerializer(UserGroup.objects.all(), many=True).data, ...)
```
**Bypass :** Filtrage par groupe
- Voit tous les groupes de l'application

**Impact :** ⚠️ **CRITIQUE** - Accès à tous les groupes

---

## 🟡 3. Affichage et filtrage de données

### `legal/views/dashboard.py`

#### `get_context_data()` - Ligne 54
```python
context['show_user_email'] = user.is_staff
```
**Bypass :** Masquage des emails utilisateurs
- Les staff voient les emails des utilisateurs dans le dashboard

**Impact :** ⚠️ **MOYEN** - Accès aux informations personnelles

#### `get_context_data()` - Ligne 67
```python
if user.is_staff or user.is_superuser:
    is_group_admin = True
```
**Bypass :** Vérification d'admin de groupe
- Considéré comme admin de groupe automatiquement

**Impact :** ⚠️ **MOYEN** - Permissions d'admin

#### `get_context_data()` - Ligne 80
```python
if not user.is_staff:
    params["user_uuid"] = str(user.uuid)
```
**Bypass :** Filtrage des projets par utilisateur
- Les staff voient tous les projets de tous les utilisateurs

**Impact :** ⚠️ **CRITIQUE** - Accès à tous les projets (confidentialité)

#### `get_context_data()` - Ligne 93
```python
if user.is_staff:
    user_tokens = extract_user_tokens_from_projects(response['results'])
    email_map = get_user_emails_map(user_tokens)
```
**Bypass :** Récupération des emails utilisateurs
- Peut récupérer les emails de tous les utilisateurs ayant des projets

**Impact :** ⚠️ **CRITIQUE** - Accès aux données personnelles

---

### `legal/views/project_history.py`

#### `get_context_data()` - Ligne 30
```python
if not user.is_staff:
    params["user_uuid"] = str(user.uuid)
```
**Bypass :** Filtrage de l'historique par utilisateur
- Les staff voient l'historique de tous les utilisateurs

**Impact :** ⚠️ **CRITIQUE** - Accès à l'historique complet

#### `get_context_data()` - Ligne 43
```python
if user.is_staff:
    user_tokens = extract_user_tokens_from_projects(response['results'])
    email_map = get_user_emails_map(user_tokens)
```
**Bypass :** Récupération des emails utilisateurs
- Peut récupérer les emails de tous les utilisateurs

**Impact :** ⚠️ **CRITIQUE** - Accès aux données personnelles

#### `get_context_data()` - Ligne 64
```python
context['show_user_email'] = user.is_staff
```
**Bypass :** Masquage des emails utilisateurs
- Les staff voient les emails dans l'historique

**Impact :** ⚠️ **MOYEN** - Accès aux informations personnelles

---

### `legal/helpers.py`

#### `process_projects()` - Ligne 187
```python
if user.is_staff and email_map:
    project['user_email'] = email_map.get(str(token))
```
**Bypass :** Masquage des emails dans les projets
- Les staff voient les emails des utilisateurs propriétaires des projets

**Impact :** ⚠️ **MOYEN** - Accès aux informations personnelles

---

## 📊 Résumé par niveau d'impact

### 🔴 CRITIQUE (Sécurité et confidentialité)
1. ✅ **`subscriptions/permissions.py:203`** - Bypass complet des permissions d'abonnement
2. ✅ **`subscriptions/helpers.py:111`** - Bypass complet des quotas de traduction
3. ✅ **`legal/views/my_team.py:222`** - Accès à tous les utilisateurs
4. ✅ **`legal/views/my_team.py:275`** - Édition de tous les utilisateurs
5. ✅ **`users/views.py:51`** - Accès à tous les groupes
6. ✅ **`legal/views/dashboard.py:80`** - Accès à tous les projets
7. ✅ **`legal/views/dashboard.py:93`** - Récupération des emails de tous les utilisateurs
8. ✅ **`legal/views/project_history.py:30`** - Accès à l'historique complet
9. ✅ **`legal/views/project_history.py:43`** - Récupération des emails de tous les utilisateurs

### 🟠 MOYEN (Fonctionnalités et affichage)
1. ✅ **`legal/views/translate.py:21`** - Accès aux glossaires officiels
2. ✅ **`legal/views/translate.py:41`** - Accès à la traduction sans groupe
3. ✅ **`legal/views/my_team.py:26`** - Accès à la gestion d'équipe
4. ✅ **`legal/views/my_team.py:180`** - Statut premium automatique
5. ✅ **`writing/views.py:63`** - Accès aux fonctionnalités d'écriture sans groupe
6. ✅ **`legal/views/dashboard.py:54`** - Affichage des emails
7. ✅ **`legal/views/dashboard.py:67`** - Statut admin automatique
8. ✅ **`legal/views/project_history.py:64`** - Affichage des emails
9. ✅ **`legal/helpers.py:187`** - Affichage des emails dans les projets

---

## 🔍 Recommandations

### Sécurité
1. **Audit des permissions staff** : Vérifier que tous les bypass sont intentionnels
2. **Logging des actions staff** : Logger toutes les actions critiques des staff
3. **Séparation des rôles** : Considérer des rôles plus granulaires (admin, support, etc.)

### Code
1. **Centraliser les vérifications** : Créer une fonction utilitaire `is_staff_or_has_permission()`
2. **Documentation** : Documenter explicitement les bypass dans le code
3. **Tests** : Ajouter des tests pour vérifier que les bypass fonctionnent correctement

### Conformité RGPD
1. **Accès aux données personnelles** : Les bypass donnent accès aux emails et données utilisateurs
2. **Journalisation** : Tracer tous les accès staff aux données personnelles
3. **Limitation** : Limiter l'accès staff aux données strictement nécessaires

---

## 📝 Notes

- Les bypass pour `is_staff` sont **intentionnels** pour permettre aux administrateurs de gérer l'application
- Cependant, certains bypass sont peut-être **trop larges** et devraient être restreints
- Considérer l'ajout d'un système de rôles plus fin si nécessaire

