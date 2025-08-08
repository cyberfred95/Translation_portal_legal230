

# **Legal 230** - Portail de traduction LEXAMT

L'objectif de ce document est d'expliquer le service de traduction  **LEXAMT**. 

# Objectif commercial

L'objectif commercial du portail **LEXAMT** est de fournir au marché une solution complète et compétitive pour offrir des services de traduction en ligne de documents juridiques avec un résultat de haute qualité dans un contexte de haute sécurité. Ceci en tenant compte de divers contraintes :

- **Coût** : Le budget pour une telle plateforme est important, la stratégie adoptée avec **Custom.mt** en tant que partenaire est de répartir les coûts entre les différents clients de **Custom.mt**.
- **Temps** : Le délai de mise sur le marché est important, nous savons que d'autres acteurs de la traduction développent actuellement leur propre solution et la première entreprise offrant un service de cette qualité aura un avantage concurrentiel sur les autres. Bien sûr, : **Custom.mt** et ****Legal 230**** ont des ressources limitées, l'aspect "réutilisation" de la stratégie technique sera l'un des critères clés de la solution car cela influencera bien sûr les autres facteurs : coût et délai de mise sur le marché.
- **Indépendance** : Le portail **LEXAMT** et le portail **lexa.com** évoluent aujourd'hui à des vitesses différentes, et ils sont développés sur des bases techniques différentes, l'indépendance de ces deux composants est une force mais devient une faiblesse lorsqu'ils doivent travailler ensemble.
- **Attractivité** : La solution ne sera pas considérée par le marché comme moderne et innovante sans une attractivité du site web lui-même, cela signifie une bonne expérience utilisateur sur le portail et un excellent design web.
- **Simplicité** : La solution technique choisie doit être simple, lorsque la complexité augmente, cela aura un impact sur d'autres facteurs tels que le coût, le délai de mise sur le marché et les ressources nécessaires pour atteindre l'objectif.

# Définition et fonctionnalités

**lexa.com** :

Identifie le site web qui sera le point d'entrée pour la présentation et la gestion des abonnements au service (voir la liste des fonctionnalités ci-dessous). Des plug-ins standards seront utilisés autant que possible (comme _Stripe_ à des fins de paiement).

#### Fonctionnalités commerciales de Lexa.com

- Abonnement à des plans pour le site **LEXAMT**.
- Paiement.

Remarques :

Lexa.com sera développé en utilisant Wordpress CMS et une base de données _mysql_.

Les clients de ****Legal 230**** connectés à ce portail sont également appelés _utilisateurs_ dans ce document.

### Portail d'Application de Traduction LEXAMT

Développé par Custom MT pour **Legal 230** pour héberger des **services de traduction en ligne**. Ce site web comprend une partie administration (réservée aux administrateurs) également appelée site web **admin** dans ce document et une partie utilisateur. La configuration pour **Legal 230** basée sur les services custom.mt est effectuée dans la partie administration du site web. Ce site web est développé à l'aide du framework _Django_.

À des fins de test, l'adresse de ce site web est actuellement [**Legal 230**.portal.custom.mt](https://**Legal 230**.portal.custom.mt), à des fins de production, une copie de ce site web sera fournie à ****Legal 230**** pour être installée dans Oracle Cloud Infrastructure.

#### Fonctionnalités LEXAMT pour les administrateurs

- Configuration de la solution .
  - Configuration de la traduction par IA.
    - Liste des IA et informations d'identification.
    - Définition des modèles.
- Synchronisation des domaines entre _TAP_ et **_Custom.mt_**_.
- Suivi des statistiques des clients de ****Legal 230****.
- Tableau de bord des statistiques de ****Legal 230****.

Remarques :

**Domaines **Legal 230** :** Le portail reliera les domaines (Droit commercial, Propriété Intellectuelle, Droit immobilier) aux modèles dans la console **Custom.mt**. ****Legal 230**** configurera des modèles pour chaque langue prise en charge.

**Statistiques :** Cette fonctionnalité comprend des API pour obtenir les statistiques de la console dans l'application du portail à intervalles définis. Le portail intégrera une page simple qui fournira une fonction pour générer un rapport d'utilisation à la demande.

#### Fonctionnalités LEXAMT pour les utilisateurs

La partie utilisateur de l'application **LEXAMT** est le principal composant de l'interface utilisateur pour les clients des services d'IA en ligne. Le portail de traduction comprend les principales fonctionnalités ci-dessous :

- Interface utilisateur,
  - "Assistant de téléchargement".
  - Saisie manuelle de phrases à traduire
  - Sélection d'invites d'IA pour modifier le document
  - Saisie manuelle de termes de glossaire
  - Téléchargement de dictionnaire de glossaire
- Fonction de connexion
- Gestionnaire de compte utilisateur
  - Fonction de mot de passe oublié.
  - Tableau de bord du client pour les services d'IA en ligne.

Remarques :

**Glossaires :** Ils seront téléchargés sur l'application du portail et stockés sur AWS. Des fonctions de gestion de glossaire de base seront intégrées, avec l'interface utilisateur détaillée à développer dans les versions ultérieures de l'application, si nécessaire.

Les utilisateurs doivent télécharger des glossaires conformes pour que la fonction fonctionne (format csv, dédupliqué, codes de langue corrects). Les glossaires ne sont pas liés à des domaines et n'ouvrent pas une structure de décision arborescente indiquant quels glossaires afficher.

**Informations d'identification :** Voir les remarques concernant la gestion des utilisateurs dans le chapitre Remarques de **lexa.com**.

### console.custom.mt

Fourni par Custom MT, ce site web gère la logique métier (configuration) des clients de **custom.mt**. Le site web **console.custom.mt** est basé sur le framework _Django_ ; c'est un aspect important car il offrira une possible réutilisation du développement pour le portail **LEXAMT**. Le portail **_custom.mt_** est également appelé le _backend_ dans ce document ou **CCMT**. Ce site web est utilisé par tous les clients de **Custom.mt** pour l'administration des utilisateurs, le tableau de bord, la facturation et les paiements.

#### Fonctionnalités  de console.custom.mt

- Téléchargement du moteur de traduction.
- Lien entre le sous-domaine et le moteur de traduction.
- Tableau de bord des statistiques d'utilisation globales.

### **Legal 230**.com

Site web actuellement en production. Ce site web fonctionnant à l'adresse [https://**Legal 230**.com](https://**Legal 230**.com) est basé sur le _Wordpress CMS_ utilisant une _base de données MySQL_. Ce site web est le site web d'entreprise de ****Legal 230**** présentant tous les services, y compris les services de traduction hors ligne.

#### Fonctionnalités de **Legal 230**.com

- Présentation de l'entreprise et des services hors ligne. Ce site web est disponible en anglais, espagnol et français.
- Informations commerciales et marketing sur **_**Legal 230**_**_.
- Formulaire de contact.
- Lien vers le portail client pour les services de traduction hors ligne ([portail.**Legal 230**.com](https://portail.**Legal 230**.com/)).
- Lien vers les services en ligne (**lexa.com**).

Remarque :

Le lien vers le portail client permet aux clients de ****Legal 230**** de télécharger des documents et de demander des services de traduction hors ligne. Des informations d'identification sont requises. Il n'y a pas d'objectif d'avoir une fonction de connexion transparente (comme les services _SSO_) entre le site web hors ligne du client (portail _LBS_) et _TAP_.

Dans le même esprit de simplicité, lors de la première étape de la production (PS1) et en raison du nombre de clients attendus à ce stade, il n'y a pas d'objectif d'avoir une synchronisation de la liste des utilisateurs entre le portail **lexa.com** et le portail **LEXAMT**, cela sera fait manuellement par la création/mise à jour/suppression d'utilisateurs sur **lexa.com** et **TAP,** cela sera nécessaire lors de la deuxième étape de la production (PS2).

### Partenaires de Traduction **Legal 230** (_LTP_)

Partenaires de traduction est un terme générique pour identifier les entités externes, les sites web ou les applications qui ont signé un contrat de partenariat spécifique avec **Legal 230** pour utiliser les services de traduction en ligne de l'IA de **Legal 230**. Pour eux, le processus d'abonnement se fait manuellement et les clés API sont fournies par e-mail.

Ce canal de vente oblige le **site web TAP** à fournir des services par API :

- Demandes de traduction.
- Utilisations de la traduction.

### Intégration technique

Par la description des fonctionnalités dans chaque composant, nous pouvons voir qu'actuellement chaque composant a ou aura son propre processus de création d'utilisateur. Ceci est acceptable pour la première étape de la phase de production avec un faible nombre d'utilisateurs. Pour la deuxième étape avec un nombre important d'utilisateurs attendus, nous devons avoir un plan de route avec une solution technique acceptée par toutes les parties pour couvrir un processus de création unique et une fonction de connexion entre tous les composants (à l'exclusion du portail client pour les services de traduction hors ligne).

### Faits objectifs

- Le plan d'abonnement sera souscrit sur le site web **_Lexa.com_**.
- Dans la première étape de la production, l'abonnement sera propagé manuellement au portail **LEXAMT**. Dans la deuxième étape de la production, une API sera appelée pour propager cet abonnement à **LEXAMT**.
- Le composant **LEXAMT** doit être conscient du plan d'abonnement car le chargement des documents à traduire sera effectué par ce composant et la vérification de la disponibilité du crédit (crédit de traduction basé sur le nombre de mots ou la date d'expiration de l'abonnement doit être effectuée avant d'exécuter la traduction et de proposer une extension d'abonnement si nécessaire).
- Les statistiques d'utilisation des crédits de l'utilisateur doivent être partagées par tous les composants.

### Diagramme de séquence

Les diagrammes de séquence décrits ci-dessous sont des diagrammes de haut niveau servant de base de discussion. Le processus de gestion des erreurs approfondi n'est pas décrit ici mais ne doit pas être oublié. Une requête synchrone (par rapport à une requête non synchrone) peut être effectuée pour éviter les divergences.

#### Processus d'abonnement

Le processus d'abonnement permettra aux utilisateurs finaux de s'abonner aux services de traduction legal230. Pour les **Partenaires de Traduction Légale** (LTP), le processus se fait manuellement et la clé API est envoyée par e-mail. Pour le canal d'abonnement **lexa.com**, le processus est le suivant :

PS1 : Première étape de la phase de production.

PS2 : Deuxième étape de la phase de production.

La création d'utilisateur dans **lexa.com pendant PS2** se fait APRÈS que toutes les requêtes ont réussis pour permettre la gestion des erreurs et éviter les divergences entre les bases de données des composants.

#### Processus de traduction

Le processus de traduction est basé sur une API du site web **LEXAMT** pour servir les demandes de traduction des Partenaires de Traduction **Legal 230**. Avec cette solution, les LTP peuvent inclure les services de traduction en ligne **Legal 230** directement dans leur application de bureau ou leur site web. (Voir la description de l'API dans le chapitre suivant. Pour les utilisateurs de **lexa.com**, l'interface utilisateur est incluse dans le site web **LEXAMT**

Processus de traduction pour un utilisateur venant du site web lexa.com :


**Vérification de la disponibilité du crédit :**

La vérification du crédit est nécessaire pour un plan qui comprend au moins l'une des plusieurs limites. Si le crédit n'est plus disponible pour le client, une redirection est effectuée vers la page _WordPress_ présentant le plan d'abonnement par **LEXAMT**.

Processus de traduction pour les Partenaires de Traduction Légale :

Le partenaire développe sa propre interface utilisateur ou son site web et appelle l'API de demande de traduction de **TAP :**


#### Tableau de bord

Le processus de tableau de bord n'est nécessaire que pour les partenaires de traduction s'ils ont besoin de connaître les détails de la consommation pour leurs processus de facturation. Il peut ne pas être nécessaire s'ils utilisent un plan d'abonnement à prix fixe. Pour les clients du site web **lexa.com**, la fonctionnalité de tableau de bord est disponible sur **LEXAMT**.