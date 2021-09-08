CHANGELOG
=========

This changelog references the relevant changes done in this project.

This project adheres to [Semantic Versioning](http://semver.org/) 
and to the [CHANGELOG recommendations](http://keepachangelog.com/).

## CONTENTS

### [0.8] - (2021-09)

- Premier script de migration pour récupérer la donnée des Siae, Réseaux et Secteurs

### [0.7] - (2021-08)

- Correctifs docker pour déploiement prod
- Bouge le modèle Siae dans sa propre app. Ajoute des champs manquants. Renomme les DateTimeFields.
- Recrée les modèle Sector & SectorGroup dans leur propre app
- Recrée le modèle Network dans sa propre app
- API : réorganisation du code atour du modèle Siae
- API : préfixe les urls avec /api
- Admin : premiers interfaces pour les modèles Siae et Sector

### [0.6] - (2021-07)

- Intégration bootstrap
- Ajout flux de traitement SCSS/SASS
- Intégration theme ITOU
- Composants layout : base, header, footer, layout
- Première page & assets graphiques : c'est quoi l'inclusion
- Compression par défaut des assets CSS & JS

### [0.5] - (2021-07)

- Écriture des vues simplifiée (ModelViewSet et Mixins)
- Filtres sur certains champs
- Wording et endpoint
- Documentation revue
- Accès SIAE par identifiant et siret
- Ajout pagination sur liste SIAE
- Ajout date de mise à jour liste SIAE
- Nouvelle page d'accueil
- Recherche par plage de date de mise à jour

### [0.4] - (2021-07)

- Logging amélioré
- Page d'accueil primitive
- Ajout donnée QPV
- Environnement Docker optimisé

### [0.3.1] - (2021-06)

- Correction de la publication des fichiers statiques quand le déboguage de django est désactivé

### [0.3] - (2021-06)

- Ajout intergiciel de tracking utilisateur

### [0.2] - (2021-06)

- Réorganisation du code (structure fichiers, config, ...)
- Utilisation de model.querysets pour les requêtes
- Utilisation contexte du serializer pour "hasher" les identifiants

### [0.1] - (2021-06)

- Premiers pas
