# Journal des modifications

Ressources :
- [Calendar Versioning](https://calver.org/)
- [CHANGELOG recommendations](https://keepachangelog.com/)

## 2023.08.25

### Ajouté

- Recherche / Fiche
    - Admin : Affichage des conversations d'une structure (#863)
    - [Inbound parsing] Ajout du nom et prénom au formulaire de contact des structures (#858)
    - [Inbound parsing 3] Ajout d'un formulaire de contact (#843)
    - Inbound Parsing : fix serializer for incoming data #842
    - [Inbound Parsing 2]Enregistrer les records d'inbound parsing (#842)
- Dépôt de besoin
    - envoyer un e-mail à J+30 aux auteurs pour savoir si il y a eu une transaction (#865)
    - CTA sur les fiches structures (#864)
    - Admin : possibilité d'ajuster l’incrémentalité d'un besoin (#859)
- Tech
    - captcha : log error only if the user is not responsible (#868)
    - Initialiser l'Email inbound Parsing (#840)

### Modifié

- Recherche / Fiche
    - Conversations : améliorer l'affichage admin (#866)
    - [Inbound Parsing] Mise à jour des infos pratique des structures (#861)
    - Ajout de MTCaptcha sur le formulaire de contact des structures (#862)
    - Conversations : utiliser send_mail au lieu de EmailMultiAlternatives (#857)
    - Conversations : améliorer l'affichage dans l'admin (#856)
    - fix html display #854
    - [Inbound Parsing 4] Migrer vers ShortUUIDField (#854)
    - display pretty messages of conversation (#855)
- Dépôt de besoin
    - Partenaires besoins : admin : pouvoir chercher par e-mail (#852)
    - Partenaires besoins : pouvoir indiquer des notes dans l'admin (#851)
- Tech
    - fix geo perimeter flacky test (#869)
    - Refactoring : séparer Dashboard & Networks (#867)
    - Dépendances : mettre à jour le repo pointant vers raphodn (#860)
    - Admin : répare l'affichage des vues avec fieldset (#823)
    - Affichage des erreurs dans les tests, même en parallèle (#853)

### Supprimé

## 2023.07.28

### Ajouté

- Recherche / Fiche
    - ajout du filtre sur les certifications (#837)
    - filtre avancé sur l'effectif (#816)
    - filtre sur la forme juridique (#812)
- Dépôt de besoin
    - pouvoir indiquer des notes dans l'admin (#845)
    - tender siaes : add ca filter to list (#827)
    - tender siaes : add employees count filter (#826)
    - nouveau champ pour indiquer le montant exact (#821)
- Tech
    - Améliorations des requêtes "annotate" (#818)
    - Ajout du driver gecko dans l'image Docker pour les tests selenium (#814)
- Autres
    - Note : importer depuis Hubspot (#848)
    - Note : utiliser CKEditor dans l'admin (#849)
    - Note : afficher et filtrer par content_type dans l'admin (#850)
    - Utilisateurs : pouvoir indiquer des notes dans l'admin (#846)
    - Structures : pouvoir indiquer des notes dans l'admin (#847)
    - Note : ajout du champ generic foreign key (#844)
    - Nouveau modèle pour indiquer des notes (#836)
    - Entreprise : script pour rattacher les utilisateurs en fonction de leur e-mail (#830)
    - Tracker : enrichir les infos des Siae (#820)
    - Entreprise : nouveau champ pour lister les nom de domaines des e-mails (#817)
    - Créer et remplir le nouveau champ Siae.legal_form (#811)

### Modifié

- Tableau de bord
    - Tableau de bord : répare les URLs des ressources (#835)
    - Distinguer les besoins provenant de Tally vs le reste de l’API (#828)
- Recherche / Fiche
    - Recherche avancée : réparer les lenteurs (#833)
    - Laisser ouvert la recherche avancée si un champs est saisi (#819)
    - Activer les filtres avancées uniquement quand l'utilisateur est connecté (#815)
- Dépôt de besoin
    - Admin : filtres par source et par montant (#841)
    - définir une date de publication (#829)
    - Dépôt de besoin : envoyer la date de clôture dans certains e-mails (#822)
- Tech
    - Hotfix: remove unused perimeters_autocomplete_field.js #800
    - try fix tests with dummy cache in test settings (#831)
    - Fix migration file name. ref #811
- Autres
    - [Mailing listes] Segmenter l’onboarding des acheteurs selon l’inscription (#839)
    - Hotfix: Siae export command (using SiaeFilterForm). ref #815
    - Fix stuff on company email_domain_list script. ref #830
    - Affichage de la modal pour s'inscrire ou se connecter pour les utilisateurs anonymes (#825)
    - Wagtail : répare l'affichage des title (#809)
    - Entreprise : améliorations dans l'admin (#824)

### Supprimé

- Tech
    - remove useless mailjet js script (#832)

## 2023.06.30

### Ajouté

- Recherche / Fiche
    - Ajout du critère chiffre d'affaire à la recherche de partenaire (#810)
    - filtre sur les prestataires avec (ou sans) groupement (#805)
    - deux petites modifications (#799)
    - filtre sur la localisation (#793)
    - filtre sur les prestataires avec (ou sans) référence client (#791)
    - Etape 1 de la recherche avancé (#782)
    - Recherche : Ajout d'un bouton pour réinitialiser le formulaire (#773)
    - add proprety to display etp count (#778)
    - Structures : améliorer l'affichage de leur "card" (#775)
- Dépôt de besoin
    - formulaire : nouvelle étape pour poser des questions (#786)
    - fix de l'écrasement des SiaeTenders par l'admin (#804)
    - Admin : pouvoir filtrer les besoins par slug (#803)
    - e-mail de rappel aux prestataires qui n'ont pas cliqué (J+4) (#785)
    - e-mail de rappel aux prestataires qui n'ont pas cliqué (J+3) (#784)
    - filtre géo sur les prestataires concernés & intéressés (#779)
    - Fix du bouton sauvegardé en brouillon (#777)
    - ajout du logo du prestataire (#774)
    - filtre sur les prestataires concernés & intéressés (#747)
- API
    - API Entreprise : récupérer les formes juridiques (brutes) (#806)
    - add siae_kind to TenderSerializer #695
- Tech
    - Maj du theme itou vers la v0.7.1 et du footer (#776)
    - Maj du theme itou vers la v0.6.8, du header et de tarte au citron (#760)
- Autres
    - Nouveau champ Siae.group_count (#792)
    - Connexion : améliorer le message pour les nouveaux utilisateurs sans mot de passe (#797)
    - Réseaux : nouveau champ pour stocker un logo (#788)
    - Nouveau modèle pour stocker les Entreprises (#787)
    - Labels : récupérer les données de l'API ADEME RGE (#761)
    - Labels : récupérer les données d'ESUS (#767)
    - Labels : récupérer les données de RSEi (#768)
    - Labels : nouveaux champs data & logs (#769)
    - Pouvoir rattacher des labels aux structures (v2) (#763)
    - create hubspot deal on admin validation (#766)


### Modifié

- Recherche / Fiche
    - reformuler l’encart "Pas de temps à perdre" (#771)
- Dépôt de besoin
    - Fix de sauvegarde deux fois un dépôt de besoin pour mettre à jour le nombre de structures (#808)
    - ajouter le champ 'source' dans l'e-mail de notification (#757)
    - bugfix sur la liste des prestataires concernés & intéressés (#781)
    - Dépôt de besoin : formulaire : répare l'affichage de la localisation sur l'aperçu (#798)
    - Personnaliser l'expérience après le dépôt de besoin (#764)
    - Optimisation des requêtes de sauvegarde des dépôts de besoins (#794)
- Tech
    - Mise à jour de l'environnement Docker (#807)
    - Django 4.2 (#801)
    - Maj du theme itou vers la v0.7.2 (#780)
    - Mise à jour des dépendances (#802)
    - update dependencies for security (#790)
    - Tâches automatisées : améliorer les messages Slack (#758)
    - fix wagtails indexes with depencies fix (#795)
    - Fix migration naming. ref #792
- Autres
    - Utiliser un seul fichier d'initialisation pour le filtre autocomplete par périmètre (#800)
    - Pouvoir rattacher une entreprise à un utilisateur (#789)
    - Structures : quelques petites modifications (#783)
    - Hotfix: move link in footer. ref #776
    - Hotfix: fix display & padding after new theme. ref #760
    - Hotfix: Header button margin. ref #760
    - Hotfix cases Siae without siret. ref #761
    - Admin : Fix de l'erreur 500 à la validation des besoins( hubspot api call) (#772)
    - Mise à jour de la popup d'authentification (#770)
    - Hotfix: siae_user.full_name in Siae completion reminder task. Other fixes. ref #753
    - Connexion : rediriger les acheteurs vers le moteur de recherche (#759)

### Supprimé

## 2023.05.26

### Ajouté

- Dépôt de besoin
    - afficher les questions dans la page détail d'un besoin (#749)
    - cleanup du formulaire (#743)
    - nouveau modèle TenderQuestion (#742)
    - envoyer un e-mail de rappel aux prestataires qui se sont montrés intéressés (#732)
    - modification du CTA (#734)
    - nouveau champ pour stocker les données venant de l'API (#730)
    - add extra data to the tender serializers
    - make email lower on tender save (#741)
    - Création d'un utilisateur dans l'appel d'api pour la création du dépôt de besoin (#740)
- Autres
    - Structures : envoyer un e-mail de rappel aux prestataires qui ont une fiche incomplète (#753)
    - Structures : nouveau champ pour logger certaines informations (#752)
    - Structures : alternative pour filtrer plus simplement par périmètre (#751)
    - Header : ajout d'un lien vers la recherche (#748)
    - Nouveau modèle pour stocker les labels (#746)
    - Admin : améliorer le rendu des CheckboxSelectMultiple (#736)
    - Ajout de la section "pourquoi faire appel à un prestataire inclusif" dans wagtail (#737)

### Modifié

- Recherche / Fiche
    - Fiche structure : modification du CTA (#756)
- Dépôt de besoin
    - Renommer le bouton d'action de la dernière étape du dépôt de besoin (#754)
    - Dépôt de besoin : afficher le nom de l'entreprise de l'acheteur (#733)
- Tech
    - Refactoring : déplacer les constants géographiques (#739)
    - Move common stuff to utils folder (#738)
- Autres
    - Inscription : rediriger les acheteurs vers le moteur de recherche (#755)
    - Header : renommer la solution Valoriser en Auditer (#750)

### Supprimé

## 2023.04.28

### Ajouté

- Tableau de bord
    - Réseaux : page intermédiaire avec le détail du besoin (#718)
    - Réseaux : page détaillée avec la liste des adhérents notifiés par une opportunité donnée (#710)
    - Réseaux : page avec la liste des opportunités commerciales de ses adhérents (#709)
- Dépôt de besoin
    - envoyer un e-mail de rappel aux prestataires qui n'ont pas cliqué (#723)
    - afficher dans certains cas l'email de Sofiane dans les coordonnées de contact (#728)
    - TenderSiae: add email_click_reminder queryset. add tests. ref #723
- Home
    - Ajout d'une section "Nos fonctionnalités" sur la page d'accueil (#713)
- Tech
    - Pouvoir anonymiser des emails (#724)

### Modifié

- Tableau de bord
    - améliore l'UX du formulaire de modification de sa structure (#714)
    - Reseaux: add badge Nouveauté. ref #709
- Dépôt de besoin
    - élargir la liste des structures intéressées (#712)
    - répare l'envoi d'e-mails aux auteurs des besoins incrémentaux (#722)
    - légère modification de l'objet de l'email envoyé aux structures (#721)
    - changer le CTA en fonction du type de besoin (#717)
    - rendre certains champs facultatifs (#729)
    - afficher un WYSIWYG pour les champs text (#716)
- Home
    - maj du bandeau "impact" (#719)
    - modifier le message du bandeau "impact" (#715)
- Recherche / Fiche
    - Mise à jour de l'ui de la page de résultat (#563)
- API
    - petite amélioration de la documentation (#731)
- Tech
    - Accessibilité : ajout des title sur les breadcrumbs (#727)
    - Mise à jour des dépendances (#726)
    - Refactoring : séparer Dashboard & Favorites (#720)
- Autres
    - Hotfix task name in Tendersiae contact click reminder #732
    - Fix parameter name in Tendersiae contact click reminder workflow. Update cron. ref #732
    - Rename tendersiae_reminders to tendersiae_contacted_reminders for clarification. ref #723
    - Additional fixes on tendersiae contacted reminder workflow. ref #723
    - Fix Tender.import_raw_object set in api create. ref #730
    - Hotfix: mismatch in cron commands. ref #723
    - Hotfix: remove Newsletter link in footer (modal not working). ref #725
    - Header : remplacer Newsletter par un lien vers une ressource (#725)
    - Fix: escape html tags in tender detail. v2. ref #716
    - Fix: escape html tags in tender detail. ref #716
    - Fix map z-index. Also fix form autocomplete height. ref #653

### Supprimé

## 2023.03.31

### Ajouté

- Tableau de bord
    - ajout d'illustrations (#708)
    - créer une nouvelle section "Favoris" (#703)
- API
    - endpoint pour récupérer la liste des montants des besoins (#701)
    - endpoint pour récupérer la liste des types de besoins (#700)
    - pouvoir déposer un besoin d'achat via l'API (#695)
- Tech
    - Ajout d'un script de génération de automatique changelog (#678)
- Autres
    - Fiche : nouveau bouton vers Annuaire Entreprises (#704)
    - Header : bouger le bouton "Favoris" dans le menu "Mon espace" (#702)
    - Ajout de la possibilité d'ajouter de la publicité modifiable depuis le backoffice (#690)

### Modifié

- API
    - indiquer la source et le status lors d'un dépôt de besoin (#699)
    - déposer un besoin avec une localisation et des secteurs (#697)
- Home
    - Migrer la homepage sur wagtail (#696)
    - Etape 2 de la migration de la page d'accueil vers le cms (#706)
    - homepage: changer le text du hero
    - hotfix stats of homepage
    - hotfix homepage sections and display alert
- Tech
    - Flatpages : expliciter les urls pour éviter les conflits avec Wagtail (#711)
    - Maj du theme itou vers la v0.6.1 (#692)
- Autres
    - Réseau : page d'accueil via son tableau de bord (#705)
    - Correction du poste qui n'était pas enregistré à l'inscription pour les acheteurs (#698)

### Supprimé

## 2023.03.10

### Ajouté

- Tableau de bord
    - Formulaire de modification d'un Siae : ajouter un encart pour s'inspirer des structures complètes (#667)
    - Après une recherche 'traiteur', ajouter les acheteurs à une list (#658)
- Recherche / Fiche
    - Après une recherche 'nettoyage', ajouter les acheteurs à une list (#675)
    - Réseaux : afficher les stats à coté des onglets (#665)
- Dépôt de besoin
    - Calcul d'impact à la création d'un besoin (#653)
    - envoi d'un e-mail aux auteurs des besoins incrémentaux (#657)
    - fix de l'url généré après une mise en relation (#688)
    - Ajout d'un conseil dans l'étape générale (#655)
    - envoyer le mail aux utilisateurs des structures (#674)
    - renommer la stat siae_interested_list_last_seen_date (#684)
    - séparer les prestataires ciblés & intéressés (#683)
    - mettre en vert le bouton "Répondre à cette opportunité" (#682)
    - cleanup de l'affichage d'un besoin (#681)
    - renommer l'URL de la liste des structures intéressées (#680)
    - optimisations sur certaines pages / requêtes (#663)
    - logger lorsque le besoin est validé (#660)
- Tech
    - Tracking : ajout d'IDs sur certains éléments (#687)
- Autres
    - Petits adjustements des stats des siaes dans le dépôt de besoin. (#683)
    - Stats : nouvelles Custom Dimension Matomo (#676)
    - Mise à jour supplémentaire de textes (#673)
    - Mise à jours de textes à destination des utilisateurs (#672)
    - Ajout d'un bouton pour inciter les utilisateurs à déposer un besoin dans la liste de favoris (#671)
    - Simplification du partage de liste de structures (#669)
    - Scroll à la liste de recherche suite à une calibration (#656)
    - Stats : ajout du formulaire NPS après une mise en relation (#685)

### Modifié

- Tableau de bord
    - fix Siae stat display again. (#512)
- Dépôt de besoin
    - Fix line-break on Tender siae stats. (#683)
    - Fix typo in Tender set_validated. (#660)
    - fix amount required (#670)
- API
    - ajouter le champ Siae.logo_url (#689)
- Tech
    - Mise à jour des dépendances (#664)
- Autres
    - Fix du bug du calcul de l'impact social à la création de dépôt de besoin (gestion du cas 750k-1M) (#679)

### Supprimé

## 2023.02.27

### Ajouté

- Recherche / Fiche
    - Mailjet : après une recherche "traiteur", ajouter les acheteurs à une liste
    - Scroll à la liste de recherche suite à une calibration
- Dépôt de besoin
    - Log lorsque le besoin est validé
    - envoi d'un e-mail aux auteurs des besoins incrémentaux
    - Formulaire : ajout d'une aide pour le champ "titre"

### Modifié

### Supprimé

## 2023.02.13

### Ajouté

- Recherche / Fiche
    - Partage d'une liste de structure par un mailto
- Tableau de bord
    - Page "animer mon réseau" : ordonner les structures par nom ; filtre par région
- Contenu / Blog
    - Nouvelles pages "Conditions générales d’utilisation" & "Conditions générales d’utilisation de l'API" & "Politique de confidentialité"
- Dépôt de besoin
    - Formulaire : ajouter une question sur le montant des dépôts de besoins
    - Admin : ajout de filtres complexe pour le dépôt de besoins dans l'admin
- Données
    - Stats : utiliser Matomo UserID

### Modifié

- Dépôt de besoin
    - modification de l'e-mail envoyé aux structures concernées
- Données
    - Réparé la synchro avec le C1
- Tech
    - Mise à jour du Thème
    - Tech : mise à jour de Django (v4.1.6)

### Supprimé

## 2023.01.30

### Ajouté

- Tableau de bord
    - Nouvelle page pour les partenaires liés à un réseau : afficher la liste de leur structures, et les statistiques correspondantes
- Contenu / Blog
    - Nouvelle page "calculateur d'impact social"
    - Home : pouvoir afficher un bandeau ; pouvoir modifier son contenu dans l'admin
- Dépôt de besoin
    - Admin : filtre des besoins par "utilité"
- Données
    - Admin : pouvoir rattacher un utilisateur à un réseau
    - Admin : pour chaque réseau, indiquer le nombre de structures et le nombre d'utilisateurs rattachés

### Modifié

- Dépôt de besoin
    - remonter les coordonnées de contact pour les structures qui se sont montrés intéressées + CTA à droite du besoin
    - Admin : ne pas pouvoir modifier le slug d'un besoin une fois qu'il est validé
- Données
    - CRM : ajout de la propiété incrémental dans la création de transaction hubspot

### Supprimé

- Tableau de bord
    - Favoris : enlever le bouton "Demande groupée"

## 2023.01.16

### Ajouté

- Recherche / Fiche
    - mise à jour du nom des onglets
- Dépôt de besoin
    - Admin : possibilité de renvoyer les emails des dépôts de besoins
    - Admin : filtre sur "transactionné"
    - Aperçu : afficher un encart incitant les structures à intéragir avec le besoin ("Déjà X prestataires inclusifs ont vu le besoin de ce client")
    - indiquer à l'acheteur lorsqu'un de ses besoin est en cours de validation
    - s'assurer que les besoins pas encore validés ne sont pas accessibles (le lien du besoin fonctionne seulement pour l'auteur ou les admin)
- Données
    - Admin : pouvoir indiquer pour chaque utilisateur leur typologie (Public / Privé / détail)
    - CRM : ajout des dépôts de besoins (à la création) dans les transactions hubspot
- Contenu / Blog
    - Ajout d'une page "Accessibilité" (lien dans le footer)

### Modifié

- Dépôt de besoin
    - Afficher "Sourcing inversé" au lieu de "Sourcing" (header, formulaire de dépôt)
    - Affichage dynamique du "Lien externe" (renomme si ce n'est pas un appel d'offres)
    - quelques modifs sur la notification Slack (indiquer le lieu d'intervention, le statut, la date de cloture, la question impact)
    - répare un bug pour accéder au formulaire de création de besoin (/besoins/ajouter/ marchait mais /besoins/ajouter provoquait une erreur)
    - répare un bug sur la création de besoin via l'erreur CSRF
- Contenu / Blog
    - légères améliorations UI sur les 2 calculateurs
- Tech
    - Thème : maj v0.5.7 ; homogénéisation du formulaire de dépôt de besoin, du formulaire de contact

### Supprimé

## 2023.01.01

### Ajouté

- Tableau de bord
    - Ajouter le calculateur “calibrer” dans le TDB acheteur
- Dépôt de besoin
    - différencier le lieu d'intervention des périmètres ciblés
    - Formulaire : ajout d'info bulles à l'étape de description
    - afficher une infobulle pour les vendeurs les incitant à prendre contact avec l'acheteur
    - Stat : nouvelle stat Date de clic sur le lien dans l'e-mail

### Modifié

- Dépôt de besoin
    - réduire l'affichage des secteurs d'activité aux 5 premiers
    - Changer le wording pour le contact des partenaire
    - fix des filtres de dépôt de besoins (filtre "Publié")
    - Admin : ajout d'un utilisateur par défaut lors d'un ajout de besoin depuis la prod
    - Admin : possibilité de modifier le statut du dépôt de besoin lorsqu'on est l'auteur du dépôt de besoin

### Supprimé

## 2022.12.12

### Ajouté

- Dépôt de besoin
    - Formulaire : ajout de l'étape sur l'utilité du dépôt de besoin
    - Formulaire : ajout du mode brouillon
    - Possibilité de trier les dépôts de besoins par statuts (Brouillon, Publié, Validé)
    - Affichage des dépôt de besoin par ordre de clôture
    - Dans l'aperçu, si le besoin a une date de réponse dépassée, ajouter un badge "Clôturé"
    - Admin : pouvoir indiquer si un besoin a transactionné
    - Admin : possibilité d'exporter les stats des siaes
- Contenu / Blog
    - Nouveau menu-dropdown "Solutions"
- Données
    - Nouveau tableau de bord Metabase sur la page stats

### Modifié

- Recherche / Fiche
    - Fix la vitesse du téléchargement lorsque l'utilisateur souhaite télécharger toutes les structures
- Tableau de bord
    - Fix l'affichage de "type de prestation" dans le formulaire d'édition de sa structure
- Dépôt de besoin
    - Formulaire : maj des labels et des message d'aide autour du montant et des moyens de réponse
    - Formulaire : cacher à la fin le nombre de structures dans le message de succès
    - dans l'aperçu : remonter la section contact (CTA "Répondre à cette opportunité" / les informations de contact)
    - dans l'aperçu : cacher la section contraintes techniques si elle est vide
    - dans l'aperçu : si le besoin est clotûré, cacher le bouton "Répondre à cette opportunité"
- Contenu / Blog
    - Calculateur "calibrage clause sociale" : ajoute un lien vers la liste complète des structures
    - Calculateur "références clients" : mise à jour du contenu, ajoute un lien vers la liste complète des structures

- Tech
    - Stats : améliorations sur le téléchargement
    - Thème : mise à jour v0.5.4 ; évite les retours à la ligne dans les boutons ; ajoute un peu d'espacements entre les périmètres du formulaire de recherche
    - Thème : mise à jour v0.5.5, mini-ajustements sur les TDB

### Supprimé

- Dépôt de besoin
    - enlever le mail automatique à l'auteur du besoin à J+30

## 2022.11.28

### Ajouté

- Recherche / Fiche
    - Téléchargement : modale pour demander à l'utilisateur les bénéfices du marché
- Tableau de bord
    - Acheteur : afficher un message incitant à déposer un besoin si l'utilisateur ne l'a pas encore fait
    - Structure : afficher 2 stats pour chacune des structure de l'utilisateur
- Contenu / Blog
    - Nouveau calculateur "références clients"
- Données
    - CRM : Ajout des acheteurs à l'inscription
    - CRM : Création d'un deal à la création d'un dépôt de besoin

### Modifié

- Dépôt de besoin
    - exclure par défaut les structures 'France entière', permettre aux admin de les ré-inclure
- Contenu / Blog
    - Calculateur "clause sociale" : transformation de la recherche en "GET" (ca permet d'avoir les détails de la recherche dans l'URL)
- Tech
    - améliorer l'affichage des secteurs d'activité pour éviter d'avoir "Autre" en premier
    - mise à jour des dépendances (dont Django à la v4.1.3, Python 3.10)

### Supprimé

## 2022.11.14

### Ajouté

- Contenu / Blog
    - Nouveau calculateur "calibrer votre achat"
    - Tracking du calcul de calibrations de clauses sociales

### Modifié

- Recherche / Fiche
    - Modification de l'icone de la carte
- Dépôt de besoin
    - Désélectionner par défaut la question “Utilité du Marché”
    - Changement des titres des mails transactionnels des dépôts de besoins
- Tech
    - Mise à jour du thème, changement de police du texte (on utilise maintenant celle du Design System de l'Etat)
    - Quelques améliorations sur les scripts de synchro/API du Lundi matin

### Supprimé

## 2022.10.31

### Ajouté

- Dépôt de besoin
    - Formulaire : rendre le champ numéro de téléphone obligatoire si l'utilisateur est anonyme
    - permettre aux structures non concernées par un besoin (mais à qui on aurait partagé le lien du besoin), d'afficher les contacts de l'acheteur et de se montrer intéressé
    - Stats : pour chaque besoin validé, rajouter maintenant dans les "logs historiques" le nombre de structures contactées ainsi que le nombre de partenaires contactés
    - permettre à certains partenaires de voir directement les coordonnées de contact des acheteurs
- Contenu / Blog
    - Articles : pouvoir ajouter un CTA "publier votre besoin"
- Inscription
    - nouveaux champs pour les acheteurs afin de connaitre leur niveau de maturité

### Modifié

- Recherche / Fiche
    - pour une recherche sur une (ou plusieurs) ville, renvoyer aussi les structures qui sont dans le même département (avant on n'en renvoyait qu'une partie)
    - Affichage de 20 résultats au lieu de 10
- Dépôt de besoin
    - ajuster la fréquence des mails envoyés à l'auteur : 1ère structure intéressée ; 2è structure (nouveau :!) ; 5è structure ; toutes les 5 structures additionnelles (jusqu'à 50 : donc 12 mails max)
    - Fix d'une URL malformée lors des envois d'emails
    - Améliorer la génération du slug ("fragment d'url"), pour éviter les erreurs et de devoir les réecrire
    - Afficher les sauts à la ligne pour le champ "contraintes techniques"
    - envoyer le titre du besoin à Mailjet (pour pouvoir l'afficher dans les templates)
    - Admin : rajoute une colonne avec la date de validation ; filtre par type de structure
- Contenu / Blog
    - modifier le lien CTA des fiches ESAT & EA, les faire pointer sur une de nos ressources
    - sur le page /partenaires/ renommer les CTA Gesat & Handeco et les faire pointer vers un Google Form
- Tech
    - clean des messages généré par les scripts "automatiques"
    - Mise à jour de Wagtail à la v4
    - Mise à jour de Django à la v4.1.2
    - Thème : mise à jour v0.5.2

### Supprimé

## 2022.10.17

### Ajouté

- Recherche / Fiche
    - transformer une recherche en dépôt de besoin (CTA + indiquer les périmètres et les secteurs d'activité)
- Dépôt de besoin
    - nouveau champ "Ouvert à la co-traitance ?" (modèle de donnée, formulaire, admin)
    - modale de confirmation pour mettre un peu de friction avant d'afficher les contact
    - Formulaire : finir par 2 questions pour mesurer l'impact du marché (pour identifier les besoins qui n’étaient pas destinés au ESI)
    - logger des infos supplémentaires lors d'envois d'emails (pour aider à débugger ensuite)
    - Admin : pour chaque structure, avoir le nombre et le lien vers les besoins concernés
- Contenu / Blog
    - Home : nouvelle section "labels & certifications"
- Tech
    - Documentation : petite liste pour expliciter les termes en anglais dans le code

### Modifié

- Recherche / Fiche
    - Hotjar : ajout d'un event lors du click sur le bouton "Afficher les coordonnées" (utilisateurs connectés)
- Dépôt de besoin
    - Admin : ajout du champ "source"
    - réparer certaines erreurs qui pouvaient arriver dans le parcours "CSRF" (suite à l'ajout des nouveaux champs)
    - répare le fait que des utilisateurs SIAE pouvaient voir des besoins non-validés dans leur TDB
- API
    - répare l'erreur pour accéder à la documentation
- Tech
    - mise à jour de Django v4.0.8

### Supprimé

- API
    - enlève les endpoints du CMS

## 2022.10.03

### Ajouté

- Recherche / Fiche
    - afficher une banière dans les résultats pour pousser au dépôt de besoin
- Dépôt de besoin
    - rendre le formulaire accessible à tous les utilisateurs (même les utilisateurs anonymes)
    - ajout d'une case à cocher pour demander à l'acheteur si il souhaite partager le montant de son besoin
    - demander le nom de l'entreprise aux utilisateurs anonymes
    - Admin : indiquer pour chaque utilisateur le nombre de dépôt de besoins déposés
- Tableau de bord
    - nouveau bandeau pour les utilisateurs "SIAE" qui ne sont pas encore rattachés à une structure
- Inscription
    - Admin : indiquer la source de la création de compte utilisateur (formulaire d'inscription ou formulaire de dépôt de besoin)

- Tech
    - Meta titles & description sur les pages clés du site
    - Message d'erreurs en cas de problèmes sur les taches asynchrones (synchronisation avec c1, etc...)

### Modifié

- Dépôt de besoin
    - fix sur l'affichage des boutons "Précédent" et "Suivant" (ils étaient inversés)
    - réparé certaines erreurs lors du remplissage du formulaire pour les auteurs anonyme qui ont leurs erreurs CSRF
    - élargissement du choix des montants
- Tech
    - thème : mise à jour, homogénéisations sur les formulaires d'authentification

### Supprimé

## 2022.09.19

### Ajouté

- Contenu / Blog
    - Home : nouvelle section étude de cas
- Dépôt de besoin
    - ajout de textes d'aides sur le formulaire
- Tech
    - Tracker géré dans l'application
    -  Import des utilisateurs dans metabase (avec la synchro)

### Modifié

- Dépôt de besoin
    - Formulaire : le champ "montant" devient obligatoire lorsqu'il s'agit d'un type "Appel d'offre"
- Tech
    - Modification de la page utilisateur dans l'admin pour chargement plus rapide

### Supprimé

## 2022.09.05

### Ajouté

- Tableau de bord
    - Ressources : ajout des images
    - Ajout du nombre de collaborateurs par structure
- Données
    - CPV : table de correspondance à mettre à jour directement dans l'admin

### Modifié

- Dépôt de besoin
    - fix de l'erreur d'envoi de mail des feedback à j+30
- Tableau de bord
    - Ressources : affichage par types d'utilisateurs ; redirection sur chaque catégorie en fonction du type d'utilisateurs
- Tech
    - Mise à jour de la version de wagtail (petits changement dans l'interface CMS)
    - Mise à jour de la version de python
    - Mise en place d'un bot pour nous alerter des nouvelles mis à jours de librairies à faire

### Supprimé

## 2022.08.08

### Ajouté

- Dépôt de besoin
    - créer les besoins malgrès l'erreur CSRF (je récupère la donnée du formulaire, c'est transparent pour l'utilisateur)
- Tech
    - Stats : on stock la date de la dernière visite sur le tableau de bord
    - Stats : on stock la date de la dernière visite sur la page "liste des besoins"

### Modifié

- Recherche / Fiche
    - ajustements sur le formulaire (style, alignement, bug du select caché par le header, badgers pour les périmètres sélectionnés)
    - fix sur le dropdown qui avait des comportement bizarre
    - mise à jour du style du bouton "Télécharger la liste"
- Dépôt de besoin
    - mise à jour du style du bouton "Télécharger la liste" sur la page des structures intéressées
    - mettre les notifications de nouveaux besoins dans un canal Slack séparé
- Tableau de bord
    - Tableau de bord : v2 pour les utilisateurs "structures"
    - Tableau de bord : v2 pour les utilisateurs acheteurs/partenaires (sans la recherche)
- Tech
    - Mise à jour du thème v0.4.9

### Supprimé

## 2022.07.18

### Ajouté

- Recherche / Fiche
    - nouvel onglet avec recherche par "Nom" (ou "Enseigne") ou "SIRET"
    - multi-selection sur les champs "Type de presta" et "Réseau"
    - Fiche : afficher le badge QPV ou ZRR si concernée
- Dépôt de besoin
    - permettre aux utilisateurs anonyme d'accéder à un besoin si ils ont l'URL. Et afficher une modale freemium lors du clic sur "Je souhaite répondre à ce besoin"
    - notifier dans un canal Slack à chaque échec du formulaire (erreur CSRF)
    - indiquer dans l'email aux structures les secteurs d'activité & périmètre qu'elles ont sélectionnés
    - garder une trace des envois effectués aux partenaires
- Tableau de bord
    - barre de complétion affichée sur la carte de sa structure
    - afficher le logo à coté du nom de la structure

### Modifié

- Recherche / Fiche
    - ordonner par défaut par date de dernière mise à jour
- Dépôt de besoin
    - renommer le bouton "Afficher les coordonnées" en "Répondre à cette opportunité"
    - Admin : pouvoir chercher un auteur avant de le sélectionner
- Contenu / Blog
    - interverti les boutons "Mon profil" et "Tableau de bord"
    - ajout d'icones sur les liens dans le dropdown
- Tech
    - mise à jour de Django à la version 4.0.6
    - remplacer une librairie qui avait une faille de sécurité (httpx par requests)

### Supprimé

- Tableau de bord
    - retirer la section "Mon profil", la rendre accessible depuis le header

## 2022.07.04

### Ajouté

- Recherche
    - multi-périmètres
- Dépôt de besoin
    - Envoi d'un email à l'auteur 30j après la validation de son besoin (pour feedback)
    - Permettre à l'auteur de télécharger la liste des structures intéressées (avec leur informations de contact)
- Contenu / Blog
    - Home : nouvelle section bandeau de logos

### Modifié

- Recherche / Fiche
    - modifier le message (et le CTA !) lorsqu'il n'y a aucun résultats retournés
    - remonte le bouton "télécharger la liste"
    - fiche : cacher/déplier les références clients si il y'en a plus de 6
- Dépôt de besoin
    - remplacé "déposer" par "publier" pour homogénéiser
- Contenu / Blog
    - Dans la section ressources, enlever la carte "groupement" "restauration" pour remonter le bouton "découvrir toutes nos ressources" à la 2e ligne
- Tech
    - répare une erreur récurrente lors de l'envoi des messages à Slack

### Supprimé

## 2022.06.20

### Ajouté

- Dépôt de besoin
    - Formulaire en 4 étapes
    - Nouveau filtre par type de prestation
    - Ajout des placeholder et help_text manquants
    - Ajoute un spinner sur le bouton "Publier" pour indiquer à l'utilisateur que ca mouline
    - Après la soumission du formulaire, afficher à l'acheteur le nombre de structures concernées

### Modifié

- Dépôt de besoin
    - Pour les administrateurs, la modification d'un besoin non validé recalcule le nombre de structures concernées
    - Fix du bug qui empêchait de revenir en arrière à la dernière étape du formulaire
    - Fix du bug sur la vérification de la présence du lien externe. désactiver le bouton de soumission post-soumission pour éviter le double clic
    - Fix l'affichage des périmètres sélectionnés à la première étape (qui disparaissaient si on revenait en arrière)
    - Ajout de la liste des partenaires
- Tech
    - Mise à jour du thème (v0.4.5)

### Supprimé

## 2022.06.06

### Ajouté

- Dépôt de besoin
    - Ajout d'un modèle "Partenaire de dépôt de besoins", pour partager le dépôt de besoin à des partenaires

### Modifié

- Dépôt de besoin
    - Fix de l'erreur d'affichage du dépôt de besoin (un utilisateur avec plusieurs SIAES)
- Recherche / Fiche
    - Fiche structure : bouton "Afficher les coordonnées" en vert
- Tableau de bord
    - Adopter d'une structure : rediriger vers le formulaire de modification de la fiche
- Contenu / Blog
    - Ajustement de la home page, changer le wording, le style des boutons, l'espacement
    - Fix : la home page ne se mettait plus à jour (stats, header), c'est réparé
    - Mise à jour du thème (sur-header)
- Données
    - Export : ajoute une colonne "Lien vers le marché" dans l'export Excel (avec l'URL de la structure sur le marché)
    - Synchro avec le C1 : modif pour remplir d'avantage le champ "contact_email" (et script lancé sur 1078 structures à qui on a rempli le champ "contact_email" grâce au champ "admin_email")

### Supprimé

- Recherche / Fiche
    - Cacher la "pub" sur les favoris
- Données
    - Cacher les structures OPCS de la recherche et des téléchargements Excel

## 2022.05.18

### Ajouté

- Mailjet
    - Ajout des acheteurs qui font des recherches à une liste
    - Ajout des emails des nouvelles structures récupéré lors de l'import C1 à une liste
- Dépôt de besoin
    - Afficher une notif à l'utilisateur indiquant le nombre de nouvelles structures intéressées
    - Ajout de l'option "France entière"
    - Notifier par email l'auteur du besoin lorsqu'il est validé/envoyé aux structures
    - Admin : pouvoir accéder à la liste des structures intéressées

### Modifié

- Dépôt de besoin
    - afficher les saut de ligne dans la description
    - pour l'acheteur, cacher le badge "type de besoin", afficher un badge "en cours de validation" si pas encore validé
    - pour les vendeurs, changer le wording pour la section coordonnées du besoin
    - Modification de l'intitulé Sourcing pour les ESI
    - Fix de l'affichage des infos de contacts
    - Fix du problème d'icone des dates dans le formulaire de dépôt
    - Ajout du pluriel à appel d'offre
    - Faute d'ortographe "Appel d'offre" --> "Appel d'offres"
- Contenu / Blog
    - Mise à jour du texte d'Handeco
    - Fix du css du CMS (images et vidéos embarqués)
- Tech
    - Thème : mise à jour (impact sur le favicon et sur les breadcrumbs)
    - Mise à jour des dépendances

    ### Supprimé

## 2022.04.28

### Ajouté

- Dépôt de besoins
    - statistiques d'envoi, de clic et d'affichage des coordonnées entre les besoins et les Siae
    - Envoi aux partenaires identifiés quand le dépôt de besoin est validé
    - Validation et envoi des dépôts de besoin depuis l'interface d'administration django
    - Mise à jour du formulaire de création pour correspondre davantage au thème
    - Notifier (par email et slack) les admins quand un dépôt de besoin a été ajouté par un acheteur
    - Notifier les acheteurs lorsque une 1ère structure est intéressée (puis toutes les 5 structures intéressées)
- Blog
    - Nouvelle fonctionnalité CMS
- Inscription / Connexion
    - Nouveau champ optin pour partager les données de contacts des Siaes à des partenaires externes
- Groupements
    - Nouvelle page qui les liste tous (/groupements)
    - Carte sur la home pour pointer vers cette nouvelle page
- API
    - ajouter le champ "is_active" dans la liste des structures, et comme champ filtrable
- Tech
    - Ajout du script Matomo Tag Manager
    - Ajout d'ids HTML sur certains liens et boutons
    - Stats : 2 nouveaux boutons dans l'admin : pour télécharger la liste enrichie de tous les téléchargements et de toutes les recherches
    - Stats : envoyer aussi "siae_id" et "results_count" lorsque c'est pertinent (fiche vue, résultats de recherche, etc)

### Modifié

-  Recherche / Fiche
    - Mettre le bouton "Afficher les coordonnées" en vert
- Dépôt de besoins
    - Modifié le champ montant en champ select
    - Afficher pour les siaes uniquement les dépôts de besoins qui sont validé et dont la date est supérieur à la date du jour
    - Petites modifications d'affichage
- Blog
    - Mise en forme des pages de blog pour qu'elles correspondent davantage au thème
- Inscription / Connexion
    - Rediriger les utilisateurs SIAE vers leur tableau de bord
- Admin
    - clarifier la différence entre structure "active" et "masquée"
    - permettre de modifier le champ "masquée"
- Tech
    - Enrichir les données de test pour les recettes jetables
    - Passage à postgres14
    - Stats : cleanup en profondeur (suppression d'evenements inutile, en doublon, etc)

### Supprimé

## 2022.03.25

### Ajouté

- Données
    - Ajouter la notion de groupement (+ ajouté une liste de 19 groupements)
- Dépôt de besoins
    - Formulaire de dépôt de besoins des acheteurs
    - Matching des besoins avec les structures du marché et envoi d'e-mails
- Inscription / Connexion
    - inscription automatique des utilisateurs inscrits sur des listes de contacts spécifiques mailjet.
- Admin
    - Ajout de l'option superuser
    - Ajout d'un champ pour stocker la date de génération des tokens

### Modifié

- Tableau de bord
    - Pouvoir se rattacher à un groupement dans le formulaire de modification de sa structure
    - Afficher l'Enseigne plutôt que la Raison sociale si l'information est remplie (comme sur les pages recherche & fiche)
- Tableau de bord
    - Ajout d'un nouveau champ "Réseau social" pour les structures (formulaire de modification + fiche)
- Inscription / Connexion
    - Cacher le bouton "Newsletter achat" pour les utilisateurs connectés

### Supprimé


## 2022.03.11

### Ajouté

-  Recherche / Fiche
    - Afficher les tags "QPV" & "ZRR"
- Admin
    - Permettre de créer et modifier certaines structures
- Données
    - Mise à jour automatiques des coordonnées GPS lorsque le champ "adresse" d'une structure est modifié

### Modifié

- Tableau de bord
    - Collaborateurs : pouvoir supprimer un autre utilisateur
    - Pouvoir modifier les champs provenant des API dans le formulaire de modification de sa structure
    - Meilleure gestion des authorizations (et des redirections lorsque l'utilisateur n'est pas connecté)
-  Recherche / Fiche
    - Le clic sur une fiche ESI ouvre un nouvel onglet
    - Refonte du CSS autour du bouton "Afficher les coordonnées"
    - Thème : utiliser les RemixIcons

### Supprimé

## 2022.02.28

### Ajouté

- Tableau de bord
    - Permettre à un utilisateur de faire une demande de rattachement à une structure déjà inscrite
    - Permettre à l'utilisateur d'une structure de gérer les demandes de rattachements à sa structure
- Données
    - Script pour récupérer le nombre d'ETP des structures depuis le C2
    - Nouveau champ `signup_date` pour mesurer l'évolution du nombre de structures inscrites
    - Nouveau champ `content_filled_basic_date` pour mesurer l'évolution du nombre de structures avec leur fiche remplie

### Modifié

- Pages
    - Mise à jour du thème itou (icons css)
-  Recherche / Fiche
    - Renommé le terme QPV
- Tableau de bord
    - Remonté la section "Mes structures" tout en haut
    - Refonte de la carte "Structure"
    - Séparé la page "Collaborateurs" du formulaire de modification de sa structure
- Données
    - API Entreprise : renommé "Unités non employeuses" par "Non renseigné"
    - Synchonisation avec le C1 : rajouté le champ `brand` à la liste des champs synchronisés
- Tech
    - Meilleure gestion des tâches asynchrones

### Supprimé

## 2022.02.11

### Ajouté

-  Recherche / Fiche
    - Mise en avant de la fonctionnalité d'envoi groupé (encart + modale + vidéo)
    - Proposer une recherche Google sur les fiches sans coordonnées
- Tableau de bord
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

## 2022.01.28

### Ajouté

- Inscription / Connexion
    - Case à cocher pour s'inscrire à la newsletter acheteur
    - Les utilisateurs structures sont automatiquement ajoutés à notre liste contact Mailjet
-  Recherche / Fiche
    - Ajout du filtre "Territoire spécifique" (QPV & ZRR)
- Tableau de bord
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
- Tableau de bord
    - Renommer "Mon espace" en "Tableau de bord"
- Admin
    - Pouvoir afficher & modifier les structures d'un utilisateur directement sur sa page
- Tech
    - Quelques bugs, typos
    - Mise à jour des packets

### Supprimé

-  Recherche / Fiche
    - Suppression de la modale "type d'utilisateur" (qui s'affichait pour les utilisateurs anonynmes)

## 2022.01.14

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

## 2021.12.31

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

## 2021.12.03

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
- Tableau de bord
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

## 2021.11.19

### Ajouté

- Pages
    - Ajout de la page /partenaires/
- Tableau de bord
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
- Tableau de bord
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

## 2021.11.05

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

## 2021.10.26

- Migration de la prod Cocorico vers la prod Django 🚀

## 2021.10

- Ajout des pages espace utilisateur
- Ajout du formulaire de modification d'une structure
- Script de migration des images vers S3
- Recherche géographique complète
- Recherche par plusieurs secteurs
- API : afficher les champs d'origine pour les Siae
- Ajout des différents trackers et tierces parties Javascript

## 2021.09

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

## 2021.08

- Correctifs docker pour déploiement prod
- Bouge le modèle Siae dans sa propre app. Ajoute des champs manquants. Renomme les DateTimeFields.
- Recrée les modèle Sector & SectorGroup dans leur propre app
- Recrée le modèle Network dans sa propre app
- API : réorganisation du code atour du modèle Siae
- API : préfixe les urls avec /api
- Admin : premiers interfaces pour les modèles Siae et Sector

## 2021.07c

- Intégration bootstrap
- Ajout flux de traitement SCSS/SASS
- Intégration theme ITOU
- Composants layout : base, header, footer, layout
- Première page & assets graphiques : c'est quoi l'inclusion
- Compression par défaut des assets CSS & JS

## 2021.07b

- Écriture des vues simplifiée (ModelViewSet et Mixins
- Filtres sur certains champs
- Wording et endpoint
- Documentation revue
- Accès SIAE par identifiant et siret
- Ajout pagination sur liste SIAE
- Ajout date de mise à jour liste SIAE
- Nouvelle page d'accueil
- Recherche par plage de date de mise à jour

## 2021.07

- Logging amélioré
- Page d'accueil primitive
- Ajout donnée QPV
- Environnement Docker optimisé

## 2021.06d

- Correction de la publication des fichiers statiques quand le déboguage de django est désactivé

## 2021.06c

- Ajout intergiciel de tracking utilisateur

## 2021.06b

- Réorganisation du code (structure fichiers, config, ...
- Utilisation de model.querysets pour les requêtes
- Utilisation contexte du serializer pour "hasher" les identifiants

## 2021.06

- Premiers pas
