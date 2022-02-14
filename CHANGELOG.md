# Journal des modifications

Ressources :
- [Semantic Versioning](http://semver.org/)
- [CHANGELOG recommendations](http://keepachangelog.com/).

## [2022.3] - 2022-02-11

### Ajouté

-  Recherche / Fiche
    - Mise en avant de la fonctionnalité d'envoi groupé (encart + modale + vidéo)
    - Proposer une recherche Google sur les fiches sans coordonnées
- Espace utilisateur
    - Nouveau typeform pour les demandes groupées
    - Nouvel onglet "Collaborateurs" dans le formulaire de modification de sa structure
- Données
    - Récupérer l'id ASP des structures depuis le C1

### Modifié

- Pages
    - Mise à jour du thème itou (icons css)
-  Recherche / Fiche
    - Réparé la recherche par périmètre
- Données
    - Ajoute l'id de l'utilisateur dans le tracking frontend
    - Ajoute des id manquants sur des `<a href=""></a>`
- Tech
    - Mise à jour de Django à la version 4.0.2

### Supprimé

## [2022.2] - 2022-01-28

### Ajouté

- Inscription / Connexion
    - Case à cocher pour s'inscrire à la newsletter acheteur
    - Les utilisateurs structures sont automatiquement ajoutés à notre liste contact Mailjet
-  Recherche / Fiche
    - Ajout du filtre "Territoire spécifique" (QPV & ZRR)
- Espace utilisateur
    - Ajout d'un bandeau Aides-territoires pour pour les utilisateurs structures
- Données
    - Champs & API pour les données ZRR
    - Import des 39 structures pénitentiaires

### Modifié

-  Recherche / Fiche
    - Affichage plus claire des réseaux de la structure
    - Afficher sur les cartes & fiches structures seulement les secteurs d'activités recherchés
    - Afficher aussi Multisectoriel dans les résultats de recherche (pour les ETTI avec beaucoup de secteurs d'activité)
    - Favoris : refonte des modales, amélioration de la vue liste sur son profil
    - Modale "freemium" : indiquer la notion de gratuité
- Espace utilisateur
    - Renommer "Mon espace" en "Tableau de bord"
- Admin
    - Pouvoir afficher & modifier les structures d'un utilisateur directement sur sa page
- Tech
    - Quelques bugs, typos
    - Mise à jour des packets

### Supprimé

-  Recherche / Fiche
    - Suppression de la modale "type d'utilisateur" (qui s'affichait pour les utilisateurs anonynmes)

## [2022.1] - 2022-01-14

### Ajouté

- Pages
    - Ajout d'une modale "freemium" sur les fonctionnalités accessibles aux utilisateurs connectés
- Inscription / Connexion
    - Envoi d'un tracking à chaque inscription pour mesure l'impact de la modale
- Tech
    - Gestion asynchrone des tâches (avec Huey)
    - Ajouté quelques scripts dans le code
    - Export régulier de toutes les structures dans un fichier

### Modifié

- Pages
    - Téléchargement immédiat de toutes les structures sur la page 'Valorises vos achats'
    - Mise à jour du thème
- Recherche / Fiche
    - Forcer l'inscription pour voir les coordonnées des structures
- Admin
    - Quelques améliorations diverses (filtres, liens entre modèles, etc.)
- Tech
    - Mise à jour de Django à la version 4.0.1
    - Modifié la génération des slug des Régions
    - Accélère l'import des périmètres sur les recettes jetables
    - Ne plus logger un message à chaque envoi du tracker
    - Réduit l'envoi d'informations à Sentry

### Supprimé

## [1.4] - 2021-12-31

### Ajouté

- Pages
    - Nouvelle page : valoriser vos achats
- Contact
    - Envoi un e-mail de confirmation aux utilisateurs de type "SIAE" (avec CTA)
- Recherche / Fiche
    - Pouvoir mettre des structures en favoris (listes d'achat)
- Tech
    - API QPV pour enrichir les fiches
    - CRON pour automatiser certaines tâches : synchro avec le C1, API Entreprise & API QPV

### Modifié

- Pages
    - Améliore le scroll vers une section donnée (évite que le header cache le haut de la section)
    - Répare le meta title de la page Statistique
    - Modale : ajout d'une option "autre"
    - Modale : s'affiche sur 2 nouvelles pages : partenaires & valoriser vos achats
    - Ajout de logos partenaires
- Recherche / Fiche
    - Légère amélioration sur l'ordre retourné par le moteur de recherche
    - Afficher un CTA sur chaque fiche pour pousser les utilisateurs Siae anonymes à se rattacher à leur fiche
- Contact
    - Ajoute un champ "type d'utilisateur" dans le formulaire
    - Ajoute du texte pour rediriger les demandes "Emplois" vers l'outil d'assistance
- API
    - publication sur api.gouv.fr
    - passage à la v1
- Tech
    - Mise à jour de Django à la version 3.2.10
    - Mise à jour de Django à la version 4
    - Configuration CORS
    - Script de déploiement

### Supprimé

## [1.3] - 2021-12-03

### Ajouté

- Pages
    - Afficher un bandeau temporairement pour certains type d'utilisateurs (acheteur, partenaires) pour les inciter à échanger avec nous
    - Ajout d'un nouveau logo de partenaire
    - Ajout d'une page `/stats` qui pointe vers notre dashboard Metabase public
- Recherche / Fiche
    - Permettre le téléchargement au format XLS
- Données
    - Script de synchronisation des structures avec le C1
    - Script de synchronisation avec les données d'API Entreprise
    - Importé ~1200 images de "réalisations" des structures depuis Cocorico

### Modifié

- Pages
    - Refonte de la page d'accueil (2 boutons actions à la place de la recherche)
    - Améliorations de l'accessibilité de la page d'accueil (navigation avec le clavier)
- Inscription / Connexion
    - Demander le type de partenaire lors de l'inscription
- Recherche / Fiche
    - Rendre les numéro de téléphone cliquable (`href="tel:`)
    - Afficher les images des "réalisations" des structures
- Espace utilisateur
    - Permettre de rajouter des "réalisations" à sa structure
- Données
    - Réparé la mise à jour en temps réel des champs `_count` de chaque structure
    - Ajout manuel de ~200 liens utilisateur-structure (source : mailing)
- Tech
    - Le thème est maintenant synchronisé directement depuis son repo github (comme le C1)
    - Ajout d'un Makefile

### Supprimé

- Pages
    - Enlevé le bandeau concernant la migration

## [1.2] - 2021-11-19

### Ajouté

- Pages
    - Ajout de la page /partenaires/
- Espace utilisateur
    - Indiquer à l'utilisateur la "complétude" de sa fiche
- Inscription / Connexion
    - Ajout d'un champ "Votre poste" pour les acheteurs
- API
    - Nouvelle url /siae/slug/{slug}/ pour trouver une structure par son slug
    - Afficher le token dans l'espace utilisateur (si il a été généré)

### Modifié

- Pages
    - Ajout du logo CNA (Conseil National des Achats) dans les partenaires
    - Lazy loading des images sur la page d'accueil pour améliorer les performances
- Recherche / Fiche
    - Clic sur l'adresse email ouvre son client email (mailto)
    - Afficher le nom du groupe lorsque le secteur est "Autre"
    - Reduction des espacements et nouvelle "card" sur la page de résultats
    - Rendre les ESAT visibles
    - Renommé "Conventionné avec la Direccte" par "Conventionné par la DREETS"
- Espace utilisateur
    - Réparé le formulaire de modification de sa structure (lorsqu'un champ readonly était manquant ; sur les références clients ; sur certains départements & régions mal importés)
    - Afficher une petite carte à coté des de l'adresse de la structure (formulaire de modification)
    - Afficher en lecture seule les données d'API Entreprise (formulaire de modification)
- Inscription / Connexion
    - Enlevé les liens vers les webinaires dans l'email post-inscription
    - Garder l'utilisateur connecté juste après son inscription
    - Eviter les erreurs de connexion à cause de majuscules dans l'email
    - Afficher un message spécifique aux utilisateurs devant réinitialiser leur mot de passe (post-migration)
- API
    - Renvoyer le champ "id" des structures
    - Amélioré la documentation concernant la demande de token
- Tech
    - Eviter les valeurs "null" sur les champs texte (base de donnée)

## [1.1] - 2021-11-05

### Ajouté

- Début du changelog (premier sprint post-migration)
- Pages
    - Lien vers la liste des facilitateurs (google doc) sur la page "C'est quoi l'inclusion"
    - Mise en avant des partenaires sur la page d'accueil (carrousel)
- Recherche / Fiche
    - Pouvoir filtrer par réseau
- Données
    - Import des ESAT (1778 structures)
- Tech
    - Pouvoir faire des review apps à la volée sur des PR ouvertes (donnée de test grâce à des fixtures)
    - Afficher un bandeau pour différencier les environnements

### Modifié

- Pages
    - Quelques mini changements sur la page d'accueil : typo, renommé le bouton Newsletter, meilleur affichage sur mobile
- Recherche / Fiche
    - Correctif pour ne pas afficher la modal pour les utilisateurs connectés
    - Correctif pour éviter de renvoyer des doublons
    - Modifié les résultats lorsqu'une ville est cherchée: les structures présentes dans la ville, mais avec périmètre d'intervention autre que Distance ou Département, sont quand même renvoyés
    - Pouvoir chercher par code postal
    - Pouvoir chercher avec plusieurs types de structures à la fois
    - Grouper les types de structures par "Insertion" et "Handicap"
    - Clarifié le nom du bouton de réinitialisation de la recherche par secteurs
    - Certaines structures n'apparaissaient pas dans les résultats (is_active=False pendant la migration). C'est réparé. Cela concernait ~1000 structures
    - Réparé la redirection lorsqu'une personne non-connectée souhaite télécharger la liste des résultats
- Inscription / Connexion
    - Réparé un bug lorsque le lien de réinitialisation du mot de passe était invalide (déjà cliqué)
    - Redirections additionnelles pour les pages de connexion et d'inscription (Cocorico)
- Formulaire de contact
    - le reply-to est maintenant l'email fourni par l'utilisateur (pour faciliter la réponse sur Zammad)
- API
    - Pouvoir filtrer les structures par réseau
    - Renvoyer d'avantage d'information dans les détails d'une structure
    - Réorganisation de la documentation

### Supprimé

## [1.0] - 2021-10-26

- Migration de la prod Cocorico vers la prod Django 🚀

## [0.9] - 2021-10

- Ajout des pages espace utilisateur
- Ajout du formulaire de modification d'une structure
- Script de migration des images vers S3
- Recherche géographique complète
- Recherche par plusieurs secteurs
- API : afficher les champs d'origine pour les Siae
- Ajout des différents trackers et tierces parties Javascript

## [0.8] - 2021-09

- Premier script de migration pour récupérer la donnée des Siae, Réseaux, Secteurs, Prestations, Labels et Références
- Ajout du modèle SiaeOffer
- Ajout du modèle SiaeLabel
- Ajout du modèle SiaeClientReference
- Ajout de Flatpages pour créer des pages statiques directement dans l'admin
- Ajout des pages d'accueil, de recherche et de fiche Siae
- Ajout des pages de connexion, inscription & réinitialisation du mot de passe
- Ajout de la page contact
- API : les données des Sector proviennent du nouveau modèle
- API : nouveaux endpoints /siae/kinds & /siae/presta-types
- Outils : ajout des packets django-debug-toolbar & django-extensions
- Outils : ajout d'un template de PR
- Outils : ajout d'un pre-commit
- Outils : ajout de Github Actions
- Màj homepage API
- Correctif SASS Django pour developpement

## [0.7] - 2021-08

- Correctifs docker pour déploiement prod
- Bouge le modèle Siae dans sa propre app. Ajoute des champs manquants. Renomme les DateTimeFields.
- Recrée les modèle Sector & SectorGroup dans leur propre app
- Recrée le modèle Network dans sa propre app
- API : réorganisation du code atour du modèle Siae
- API : préfixe les urls avec /api
- Admin : premiers interfaces pour les modèles Siae et Sector

## [0.6] - 2021-07

- Intégration bootstrap
- Ajout flux de traitement SCSS/SASS
- Intégration theme ITOU
- Composants layout : base, header, footer, layout
- Première page & assets graphiques : c'est quoi l'inclusion
- Compression par défaut des assets CSS & JS

## [0.5] - 2021-07

- Écriture des vues simplifiée (ModelViewSet et Mixins
- Filtres sur certains champs
- Wording et endpoint
- Documentation revue
- Accès SIAE par identifiant et siret
- Ajout pagination sur liste SIAE
- Ajout date de mise à jour liste SIAE
- Nouvelle page d'accueil
- Recherche par plage de date de mise à jour

## [0.4] - 2021-07

- Logging amélioré
- Page d'accueil primitive
- Ajout donnée QPV
- Environnement Docker optimisé

## [0.3.1] - 2021-06

- Correction de la publication des fichiers statiques quand le déboguage de django est désactivé

## [0.3] - 2021-06

- Ajout intergiciel de tracking utilisateur

## [0.2] - 2021-06

- Réorganisation du code (structure fichiers, config, ...
- Utilisation de model.querysets pour les requêtes
- Utilisation contexte du serializer pour "hasher" les identifiants

## [0.1] - 2021-06

- Premiers pas
