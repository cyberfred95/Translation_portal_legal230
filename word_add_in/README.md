# Lexa Word Add-in - Extension de Traduction Juridique

## Installation

1. **Prérequis**
   - Microsoft Word 2016 ou plus récent
   - Node.js 16 ou plus récent et npm installés
   - Clé API Lexa valide

2. **Installation des outils Office Add-in**
   ```bash
   npm install -g yo generator-office
   ```

3. **Installation des dépendances du projet**
   ```bash
   npm install
   ```

4. **Démarrage du serveur de développement**
   ```bash
   npm start
   ```

5. **Chargement dans Word**
   
   **Méthode 1 : Via le catalogue de compléments (recommandée)**
   - Ouvrir Word
   - Aller dans Fichier > Options > Centre de gestion de la confidentialité > Paramètres du centre de gestion de la confidentialité
   - Cliquer sur "Catalogues de compléments approuvés"
   - Ajouter le dossier du projet comme catalogue approuvé (cocher "Autoriser les sous-dossiers")
   - Redémarrer Word
   - Dans Word, aller dans **Insertion > Compléments > Mes compléments**
   - Cliquer sur l'onglet "DOSSIER PARTAGÉ"
   - Sélectionner "Lexa Traduction juridique"

   **Méthode 2 : Chargement manuel (alternative)**
   - Dans Word, aller dans **Insertion > Compléments > Télécharger des compléments**
   - Cliquer sur "Télécharger un manifeste" (en bas à droite)
   - Parcourir et sélectionner le fichier `manifest.xml` de votre projet
   
   **Méthode 3 : Via le ruban Développeur**
   - Activer l'onglet Développeur dans Word (Fichier > Options > Personnaliser le ruban)
   - Aller dans **Développeur > Compléments > Mes compléments**
   - Cliquer sur "Télécharger un manifeste"
   - Sélectionner le fichier `manifest.xml`

   **Note importante :** Si vous ne voyez pas "Mes compléments", essayez :
   - **Insertion > Compléments** (Word 365/2019+) / **Insert > Add-ins** (EN)
   - **Insertion > Applications** (Word 2016) / **Insert > My Add-ins** (EN)
   - **Insertion > Store** (versions plus anciennes) / **Insert > Store** (EN)
   
   **Termes anglais selon les versions :**
   - **Word 365/2019+** : Insert > Add-ins > My Add-ins (onglet "SHARED FOLDER")
   - **Word 2016** : Insert > My Add-ins ou Insert > Office Add-ins > My Add-ins
   - **Développeur** : Developer > Add-ins > My Add-ins
   - **Chargement manuel** : Insert > Add-ins > Upload My Add-in

## Développement

1. **Mode développement**
   ```bash
   npm run build:dev
   npm run dev-server
   ```

2. **Build de production**
   ```bash
   npm run build
   ```

3. **Validation du manifeste**
   ```bash
   npm run validate
   ```

## Utilisation

1. **Configuration initiale**
   - Ouvrir Word et cliquer sur l'onglet "Lexa" dans le ruban
   - Cliquer sur "Ouvrir Lexa" pour ouvrir le panneau
   - Cliquer sur "⚙️ Configuration" et entrer votre clé API

2. **Traduction de texte**
   - Sélectionner le texte à traduire dans le document
   - Choisir les langues source et cible
   - Optionnel: sélectionner un domaine et un glossaire
   - Cliquer sur "Traduire la sélection"

3. **Fonctionnalités avancées**
   - Inversion des langues avec le bouton ⇄
   - Sélection de domaines spécialisés (juridique, médical, etc.)
   - Utilisation de glossaires par défaut ou personnels

## Résolution des problèmes

1. **Le complément n'apparaît pas dans "Mes compléments"**
   - Vérifiez que le serveur de développement est bien démarré (`npm start`)
   - Assurez-vous que le dossier est bien ajouté aux catalogues approuvés avec "Autoriser les sous-dossiers" coché
   - Redémarrez Word complètement
   - Vérifiez que vous cherchez dans le bon onglet : "DOSSIER PARTAGÉ" et non "STORE"
   - Essayez la méthode de chargement manuel du manifeste

2. **Erreur "Nous ne pouvons pas ouvrir ce complément"**
   - Vérifiez que le serveur fonctionne sur `http://localhost:3000`
   - Ouvrez `http://localhost:3000/taskpane.html` dans votre navigateur pour tester
   - Assurez-vous que tous les fichiers sont bien générés dans le dossier `dist`

3. **Problème de certificat HTTPS (Word 365 et versions web)**
   - **Erreur :** Le complément ne se charge pas et mentionne un problème de sécurité ou une page inaccessible.
   - **Cause :** Word 365 exige des sources `https`, mais le certificat de développement local n'est pas approuvé par défaut.
   - **Solution :**
     1. Ouvrir un terminal (PowerShell/pwsh) **en tant qu'administrateur**.
     2. Naviguer vers le dossier du projet : `cd "chemin\vers\votre\projet"`
     3. Exécuter la commande : `npx office-addin-dev-certs install`
     4. Accepter l'installation du certificat.
     5. Redémarrer le serveur de développement (`npm start`).
     6. Vider le cache des compléments Office si nécessaire.

4. **Erreur JSON dans package.json**
   ```bash
   # Supprimer les lignes dupliquées à la fin du fichier
   # S'assurer qu'il n'y a qu'une seule accolade fermante à la fin
   # Vérifier la syntaxe avec :
   node -e "console.log(JSON.parse(require('fs').readFileSync('package.json', 'utf8')))"
   ```

5. **Commandes de diagnostic**
   ```bash
   # Vérifier que le serveur fonctionne
   curl http://localhost:3000/taskpane.html
   
   # Ou ouvrir dans le navigateur
   start http://localhost:3000/taskpane.html
   ```
