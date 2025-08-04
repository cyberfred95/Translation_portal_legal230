# Gestion des mails

## 1. Objectif du module de gestion des mails
Le module de gestion des mails permet de définir, d'envoyer, de suivre et gérer les emails envoyés par ```LEXA```aux utilisateurs. les fonctionalités sont les suivantes :  
- Gestion centralisée dans le menu ```ADMIN``` de ```LEXA``` pour configurer les modèles d'emails,
- Une fiablilité des envois par l'usage de la plateforme de marketing  ```activetrail.fr```,
- Une gestion multilangue des emails,
- Une séparation entre la défintion du design (dans ```activetrail.fr```) et l'envoi du mail depuis ```LEXA```.

## 5. Les gabarits dans ```activetrail.fr```
Les gabarits sont configurés dans ```activetrail.fr``` et référencés par le menu ```ADMIN``` dans ```LEXA``` via leur `template_id`. Ils permettent de standardiser les emails envoyés et de garantir une cohérence visuelle.  
Le `template_id` est obtenu en consultant l'```URL``` du gabarit lors de sa création.

### 5.1. Configuration des gabarits
Les gabarits sont définis dans le fichier `data_email.py` avec :  
- `template_id` : Identifiant unique du gabarit.  
- `subject` : Sujet par défaut de l'email.

### 5.2 Gestion des gabarits dans le menu admin
Un nouvel onglet "Gestion des mails" est ajouté dans le menu ```ADMIN``` de ```LEXA``` . Il permet :  
- De visualiser et modifier les paramètres des emails (`EmailSettings`).  
- De configurer les gabarits d'emails et leurs sujets.  
- De filtrer les paramètres par type d'email ou langue.


## 4. Les API ActiveTrail utilisées
Le module utilise les API ```activetrail.fr``` pour :  
- Envoyer des emails via l'endpoint `OperationalMessage/Message`.  
- Configurer les en-têtes HTTP pour l'authentification.  
- Utiliser les gabarits définis dans ```activetrail.fr``` pour personnaliser les emails. La personnation de l'email se fait par la mention des variables à remplacer et leur contenu lors de l'appel de l'API.

### 4.1. En-têtes HTTP et le corps de la requête
Les en-têtes incluent :  
- `Content-Type` : `application/json`.  
- `Authorization` : Clé API pour l'accès sécurisé.

Le corps de la requête inclut :  
- `email_package` : Liste des destinataires et leurs données personnalisées.  
- `details` : Informations sur le sujet, l'expéditeur et le type d'email.  
- `design` : Identifiant du gabarit et configuration de la langue.

## 2. Modifications sur le modèle de données
### 2.1. Modèles et colonnes ajoutées
Afin d'implémenter cette gestion la liste des modèles ajoutés est la suivante :

1. **Modèle  `EMAILS_EmailSettings`**  
   - `id` : Identifiant unique.  
   - `email_type` : Type d'email (ex. `USER_CREATED`, `USER_DELETED` etc).  
   - `language` : Langue de l'email (ex. `fr`, `en`).  
   - `template_id` : Identifiant du gabarit dans ```activetrail.fr```.  
   - `subject` : Sujet de l'email.  

2. **Modèle  `USERS_user`**  
   - `language` : langue de communication de l'utilisateur.
   
   **Contraintes et informations** :  
   - Les colonnes `email_type` et `language` doivent être uniques ensemble. Permettant de définir un seul email pour un couple `email_type` et `language` donné.
   - La langue qui sera utilisée est fonction de l'information portée par la propriété `language` de l'utilisateur qui défie la langue de communication avec celui-ci.
   - Une liste par défaut de définition des `email_type` est créé automatiquement lors de l'installation de la version via le signal `post_migrate` (fichier `apps.py`).  

## 6. Processus pour ajouter un email à cette gestion

L'ajout d'un nouvel email à cette gestion se fait de la manière suivante :  
1. Créer un gabarit dans ```activetrail.fr``` par exmeple par duplication et modification d'un autre gabarit et copier son `template_id` à partir de l'```URL```.
1. Ajouter un nouveau type d'email dans l'énumération `EmailType` (fichier `models.py` ou `data_email.py`).  
2. Configurer les paramètres par défaut dans `data_email.py` (ex. `template_id`, `subject`).  
4. Configurer ou modifier les paramètres dans l'interface admin.  
5. Utiliser la fonction `send_email` (fichier `send_email.py`) dans le developpement pour envoyer l'email avec les données nécessaires.

## 7. Initialisation du paramétrage des `email`

Lors de la migration le modèle **`EMAILS_EmailSettings`** est automatiquement renseigné avec la liste des types de mail en français et en anglais suivant :

| Email_type | Language | Template_id | Subject |
|------------|----------|-------------|---------|
| SUBSCRIPTION_DELETED | FR | 211810 | Lexamt.fr - Suppression de votre abonnement |
| SUBSCRIPTION_DELETED_ADMIN | FR | 212054 | Lexamt.fr - Suppression de votre abonnement |
| SUBSCRIPTION_NEED_PAYMENT_ADMIN | FR | 211809 | Lexamt.fr - Défaut de paiement détécté |
| SUBSCRIPTION_TRIALS_WILL_END | FR | 211811 | Lexamt.fr - Votre période d'essai arrive à expiration |
| SUBSCRIPTION_TRIALS_WILL_END_ADMIN | FR | 212041 | Lexamt.fr - Votre période d'essai arrive à expiration |
| SUBSCRIPTION_UPDATED_INACTIVE | FR | 211808 | Lexamt.fr - Votre abonnement est devenu inactif |
| SUBSCRIPTION_UPDATED_INACTIVE_ADMIN | FR | 212047 | Lexamt.fr - Votre abonnement est devenu inactif |
| SUBSCRIPTION_UPDATED_QUANTITY_ADMIN | FR | 211807 | Lexamt.fr - Modification de votre abonnement confirmé |
| USER_CREATED | FR | 211686 | Lexamt.fr - Bienvenue et accès à votre compte |
| SUBSCRIPTION_DELETED | EN | 211923 | Lexamt.com - Your subscription has been cancelled |
| SUBSCRIPTION_DELETED_ADMIN | EN | 212053 | Lexamt.com - Your subscription has been cancelled |
| SUBSCRIPTION_NEED_PAYMENT_ADMIN | EN | 211924 | Lexamt.com - Payment failure detected |
| SUBSCRIPTION_TRIALS_WILL_END | EN | 211925 | Lexamt.com - Your trial period is expiring |
| SUBSCRIPTION_TRIALS_WILL_END_ADMIN | EN | 212046 | Lexamt.com - Your trial period is expiring |
| SUBSCRIPTION_UPDATED_INACTIVE | EN | 211926 | Lexamt.com - Your subscription has become inactive |
| SUBSCRIPTION_UPDATED_INACTIVE_ADMIN | EN | 212052 | Lexamt.com - Your subscription has become inactive |
| SUBSCRIPTION_UPDATED_QUANTITY_ADMIN | EN | 211951 | Lexamt.com - Subscription modification confirmed |
| USER_CREATED | EN | 211927 | Lexamt.com - Welcome and access to your account |

