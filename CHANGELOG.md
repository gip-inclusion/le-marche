# Journal des modifications

Ressources :
- [Calendar Versioning](https://calver.org/)
- [CHANGELOG recommendations](https://keepachangelog.com/).

## 2023.03.10
### Ajouté
 - [#edcc4]: Après une recherche 'nettoyage', ajouter les acheteurs à une list (#675)
 - [#1b92e]: Tracking : ajout d'IDs sur certains éléments (#687)
 - [#2fe5e]: Petits adjustements des stats des siaes dans le dépôt de besoin. (#683)
 - [#a74f4]: Stats : nouvelles Custom Dimension Matomo (#676)
 - [#d3262]: Mise à jour supplémentaire de textes (#673)
 - [#94e2b]: Mise à jours de textes à destination des utilisateurs  (#672)
 - [#6d36d]: Ajout d'un bouton pour inciter les utilisateurs à déposer un besoin dans la liste de favoris (#671)
 - [#602da]: Simplification du partage de liste de structures (#669)
 - [#2a8a2]: Formulaire de modification d'un Siae : ajouter un encart pour s'inspirer des structures complètes (#667)
 - [#d1a4b]: Réseaux : afficher les stats à coté des onglets (#665)
 - [#f48b6]: Après une recherche 'traiteur', ajouter les acheteurs à une list (#658)
 - [#6abcb]: Scroll à la liste de recherche suite à une calibration (#656)
 - [#f5f17]: Stats : ajout du formulaire NPS après une mise en relation (#685)
 - Dépôt de besoin :
    - [#25ded]: Calcul d'impact à la création d'un besoin (#653)
    - [#380d9]: Dépôt de besoin : envoi d'un e-mail aux auteurs des besoins incrémentaux (#657)
    - [#bd446]: Dépôt de besoin : fix de l'url généré après une mise en relation (#688)
    - [#51c6c]: Ajout d'un conseil dans l'étape générale (#655)
    - [#16df1]: envoyer le mail aux utilisateurs des structures (#674)
    - [#93595]: renommer la stat siae_interested_list_last_seen_date (#684)
    - [#b73cb]: séparer les prestataires ciblés & intéressés (#683)
    - [#e351f]: mettre en vert le bouton "Répondre à cette opportunité" (#682)
    - [#ab8c2]: cleanup de l'affichage d'un besoin (#681)
    - [#34685]: renommer l'URL de la liste des structures intéressées (#680)
    - [#010c6]: Dépôt de besoin : optimisations sur certaines pages / requêtes (#663)
    - [#31edc]: Dépôt de besoin : logger lorsque le besoin est validé (#660)
### Modifié
- [#09cdf]: Mise à jour des dépendances (#664)
- [#6e085]: Fix line-break on Tender siae stats. ref #683
- [#e3601]: TDB: fix Siae stat display again. ref #512
- [#ba566]: Fix du bug du calcul de l'impact social à la création de dépôt de besoin (gestion du cas 750k-1M) (#679)
- [#76996]: fix amount required (#670)
- [#23195]: Fix typo in Tender set_validated. ref #660
- API:
    - [#c3233]: ajouter le champ Siae.logo_url (#689)
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
- Espace utilisateur
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

- Espace utilisateur
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

- Espace utilisateur
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

- Espace utilisateur
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
- Espace utilisateur
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
- Espace utilisateur
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
- Espace utilisateur
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

- Espace utilisateur
    - Ressources : ajout des images
    - Ajout du nombre de collaborateurs par structure
- Données
    - CPV : table de correspondance à mettre à jour directement dans l'admin

### Modifié

- Dépôt de besoin
    - fix de l'erreur d'envoi de mail des feedback à j+30
- Espace utilisateur
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
- Espace utilisateur
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
- Espace utilisateur
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

- Espace utilisateur
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
- Espace utilisateur
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
- Espace utilisateur
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

- Espace utilisateur
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

- Espace utilisateur
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
- Espace utilisateur
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

## 2022.01.28

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

## 2021.11.19

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
