# Journal des modifications

Ressources :
- [CHANGELOG recommendations](https://keepachangelog.com/)
- [Conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)
- [release-please](https://github.com/google-github-actions/release-please-action) (automated releases)
- [Semantic Versioning](https://semver.org/) & [Calendar Versioning](https://calver.org/)

## [2025.3.0](https://github.com/gip-inclusion/le-marche/compare/v2024.9.0...v2024.2.0) (2025-03-20)


### Features

* **Ajout d'un module django de guide pas à pas des utilisateurs** ([#1315](https://github.com/gip-inclusion/le-marche/issues/1315)) ([227f455](https://github.com/gip-inclusion/le-marche/commit/227f455451e9a1ce4f589143c9f51a4f00f5620f))
* **Authentification obligatoire sur l'API** ([#1628](https://github.com/gip-inclusion/le-marche/issues/1628)) ([7ac41ff](https://github.com/gip-inclusion/le-marche/commit/7ac41ffe6ae3432a309eaced23de52c4e1352fe6))
* **Prise de rendez vous à l'inscription** ([#1663](https://github.com/gip-inclusion/le-marche/issues/1663)) ([38c4219](https://github.com/gip-inclusion/le-marche/commit/38c421915f10c4b8af3a23eedad6db443f9ebbe3))
* **Admin des Besoins:** Demande de modification ou clôture d'un besoin  ([#1596](https://github.com/gip-inclusion/le-marche/issues/1596)) ([e4bc06b](https://github.com/gip-inclusion/le-marche/commit/e4bc06b6caae8505089270645f189f480ede70e2))
* Menu déroulant "Mon espace" dans le header ([#1662](https://github.com/gip-inclusion/le-marche/issues/1662)) ([e38f8a0](https://github.com/gip-inclusion/le-marche/commit/e38f8a0340c170377312cc7ecc5374c3c83a4fb8))
* Ajout de la page FAQ dans le footer ([#1649](https://github.com/gip-inclusion/le-marche/issues/1649)) ([cda59af](https://github.com/gip-inclusion/le-marche/commit/cda59af8995bca7d39b8662adb5875e16cdffe28))


### Bug Fixes

* Affichage du bandeau d'environnement ([#1648](https://github.com/gip-inclusion/le-marche/issues/1648)) ([b71da26](https://github.com/gip-inclusion/le-marche/commit/b71da263fb23e74ae1f5afe8b6b2e4b1286a8f98))
* Ajout d'un label pour le type d'utilisateur ([#1667](https://github.com/gip-inclusion/le-marche/issues/1667)) ([6f89c29](https://github.com/gip-inclusion/le-marche/commit/6f89c290c553cc8e149b6a2b3d92b9c3878cfb6e))
* bug sur les gestionnaires sur Admin ([#1638](https://github.com/gip-inclusion/le-marche/issues/1638)) ([55cac40](https://github.com/gip-inclusion/le-marche/commit/55cac40569c36b82268e63af96cf625e7d0172dc))
* bug sur les secteurs dans l'API des SIAE ([#1669](https://github.com/gip-inclusion/le-marche/issues/1669)) ([afd1a1b](https://github.com/gip-inclusion/le-marche/commit/afd1a1b34d864b92bdd9f5e895177b145e6b5fb5))
* collaborateurs: Correction du rattachement des collaborateurs sur certains navigateurs ([#1655](https://github.com/gip-inclusion/le-marche/issues/1655)) ([9a019bd](https://github.com/gip-inclusion/le-marche/commit/9a019bd0ddac723e40d433f61b396103c640fad2))
* Copie de django-fieldsets-with-inlines ([#1657](https://github.com/gip-inclusion/le-marche/issues/1657)) ([92ce844](https://github.com/gip-inclusion/le-marche/commit/92ce8443741b1bb10f159c9a2773545ae9465e3b))
* doubles imports alpineJs ([#1670](https://github.com/gip-inclusion/le-marche/issues/1670)) ([2023316](https://github.com/gip-inclusion/le-marche/commit/20233161b6cd4afc6a0076beec6052501cdb7cb4))
* duplication des siae dans l'API ([#1674](https://github.com/gip-inclusion/le-marche/issues/1674)) ([5236a55](https://github.com/gip-inclusion/le-marche/commit/5236a5570b4ac9bddabca7b98ebcedaafdec31fa))
* Fix template overload ([#1658](https://github.com/gip-inclusion/le-marche/issues/1658)) ([a82ca6e](https://github.com/gip-inclusion/le-marche/commit/a82ca6e66e092b3364da20beebef448693fae557))
* Le logout doit se faire en POST ([#1656](https://github.com/gip-inclusion/le-marche/issues/1656)) ([c723eb1](https://github.com/gip-inclusion/le-marche/commit/c723eb1ff62ddf7de3fdfcc19615bf5a0d27ca5b))
* Methode save() supprimée de l'admin des besoins ([#1665](https://github.com/gip-inclusion/le-marche/issues/1665)) ([b48b680](https://github.com/gip-inclusion/le-marche/commit/b48b6802674b3fa9b56a0ab5c01b1454d5679bdf))
* Migrer les presta_type vide des activités ([#1676](https://github.com/gip-inclusion/le-marche/issues/1676)) ([7718fd3](https://github.com/gip-inclusion/le-marche/commit/7718fd3f3f3a6dbd8e6945ec9f5d878e21cb09d9))
* Prise en charge des ids malformés dans l'API des siae ([#1675](https://github.com/gip-inclusion/le-marche/issues/1675)) ([c414da4](https://github.com/gip-inclusion/le-marche/commit/c414da40736cecdc7b1e77c95cc7b5c0c9ff54c0))
* S3: Correction de l'erreur d'envoi d'image dans l'admin Wagtail ([#1664](https://github.com/gip-inclusion/le-marche/issues/1664)) ([a0b9b61](https://github.com/gip-inclusion/le-marche/commit/a0b9b61a99224c6f92538ce834f43bb80389bedd))
* value error recherche prestataire =&gt; passage django 4.2 => 5.1 ([#1635](https://github.com/gip-inclusion/le-marche/issues/1635)) ([f1196c7](https://github.com/gip-inclusion/le-marche/commit/f1196c722f0dd20decfb982537d9ba6f1d61f242))
* Widget de secteurs d'activité buggé dans la page de signup ([#1660](https://github.com/gip-inclusion/le-marche/issues/1660)) ([a776105](https://github.com/gip-inclusion/le-marche/commit/a776105755b6ab22d7a52876175aaf856a1b7ec9))
* wrong GET ids ([#1636](https://github.com/gip-inclusion/le-marche/issues/1636)) ([3047b38](https://github.com/gip-inclusion/le-marche/commit/3047b38ed243ce9e60ab93a586314352a3e05ffd))

### Refactor
* factorisation d'un copié-collé ([#1640](https://github.com/gip-inclusion/le-marche/issues/1640)) ([c9de2f2](https://github.com/gip-inclusion/le-marche/commit/c9de2f29106655b3ea43d21562349c47348c037d))
* Supprimer mailjet ([#1632](https://github.com/gip-inclusion/le-marche/issues/1632)) ([cdc6634](https://github.com/gip-inclusion/le-marche/commit/cdc6634366f90c0eccb7db2ce450899ad9fb8853))

## [2024.9.0](https://github.com/gip-inclusion/le-marche/compare/v2024.8.0...v2024.9.0) (2025-02-03)


### Features

* Action admin pour l'anonymisation des utilisateurs ([#1624](https://github.com/gip-inclusion/le-marche/issues/1624)) ([0dc2970](https://github.com/gip-inclusion/le-marche/commit/0dc2970078a56df4405e8668b91000779105c69a))
* **Email Notifications:** Mise à jour côté Brevo du choix pour les communications Marketing ([#1639](https://github.com/gip-inclusion/le-marche/issues/1639)) ([f7b9c1a](https://github.com/gip-inclusion/le-marche/commit/f7b9c1a48259338144a30113257d45852fd3ccd5))
* **Email Notifications:** Prise en compte de la désactivation d'un groupe d'email par un utilisateur ([#1630](https://github.com/gip-inclusion/le-marche/issues/1630)) ([3bee0e0](https://github.com/gip-inclusion/le-marche/commit/3bee0e0ce20ee69ab96f9e7137de682ae26987fe))
* Retirer la co-traitance ([#1623](https://github.com/gip-inclusion/le-marche/issues/1623)) ([d3676d1](https://github.com/gip-inclusion/le-marche/commit/d3676d161d3972745f4024fc18e9dd0e1b36e903))
* suppression de la synchro c2 c4 ([#1633](https://github.com/gip-inclusion/le-marche/issues/1633)) ([88c131e](https://github.com/gip-inclusion/le-marche/commit/88c131edaa8f492f226b63539042bf5518aa088b))


### Bug Fixes

* **Activités des structures:** Correction du formulaire d'édition des activités ([#1625](https://github.com/gip-inclusion/le-marche/issues/1625)) ([432d7a2](https://github.com/gip-inclusion/le-marche/commit/432d7a256646bb5d410e1750907cbb6df4d93a82))
* Changement de conditions de synchronisation des DDB vers le crm brevo ([#1622](https://github.com/gip-inclusion/le-marche/issues/1622)) ([393f227](https://github.com/gip-inclusion/le-marche/commit/393f227e3b3f21e3615445799a2dbcebdd9258e6))
* **Email:** Retour sur l'enregistrement du log avant envoi ([#1629](https://github.com/gip-inclusion/le-marche/issues/1629)) ([65a2fe6](https://github.com/gip-inclusion/le-marche/commit/65a2fe6653007257732df4365c1063f0726a201d))
* Flacky test causé par un mot de passe aléatoire non valide ([#1621](https://github.com/gip-inclusion/le-marche/issues/1621)) ([561c066](https://github.com/gip-inclusion/le-marche/commit/561c06693615b5553ac48d65d666685eac7c010a))
* **Structures:** Correction sur le contrôle d'unicité du nom commercial ([#1606](https://github.com/gip-inclusion/le-marche/issues/1606)) ([171abff](https://github.com/gip-inclusion/le-marche/commit/171abff7a5c4aaaae933356a22768842eb2a33a3))

## [2024.8.0](https://github.com/gip-inclusion/le-marche/compare/v2024.7.0...v2024.8.0) (2025-01-02)


### Features

* **Admin:** Ajout de 'contact_phone' dans la recherche ([#1575](https://github.com/gip-inclusion/le-marche/issues/1575)) ([2dff083](https://github.com/gip-inclusion/le-marche/commit/2dff0830c369304c2c2db3df4e477e297584c4b9))
* Ajout d'attributs dans Brevo pour les structures ([#1513](https://github.com/gip-inclusion/le-marche/issues/1513)) ([f41f5c5](https://github.com/gip-inclusion/le-marche/commit/f41f5c52b51808eb921f370aa5a5022be1a7dfdb))
* ajouter le tri des activités dans l'admin par date de modification ([1db3999](https://github.com/gip-inclusion/le-marche/commit/1db399932dc524898e37636634a95f061b412cf2))
* Conversations: anonymisation des données ([#1618](https://github.com/gip-inclusion/le-marche/issues/1618)) ([4d65073](https://github.com/gip-inclusion/le-marche/commit/4d650732beb750840b43d490f065d429bfbe65c6))
* **Email Notifications:** Ajout du formulaire d'édition des préférences ([#1595](https://github.com/gip-inclusion/le-marche/issues/1595)) ([b50530a](https://github.com/gip-inclusion/le-marche/commit/b50530afd8dd60d5e5d5f3939468e85a707c1cfa))
* **Siae:** Permettre aux structures de changer leur nom commercial ([#1552](https://github.com/gip-inclusion/le-marche/issues/1552)) ([9c32349](https://github.com/gip-inclusion/le-marche/commit/9c32349e3761b0f23e539b7decbb034fb5cb229e))
* Suppression des données personnelles ([#1607](https://github.com/gip-inclusion/le-marche/issues/1607)) ([ec4fbbf](https://github.com/gip-inclusion/le-marche/commit/ec4fbbfc5caaa70110729be8683d13bb640891b7))
* Whitelist des ips de Brevo pour inbound emails ([#1620](https://github.com/gip-inclusion/le-marche/issues/1620)) ([e33ed12](https://github.com/gip-inclusion/le-marche/commit/e33ed1229724788a646d2c2849b96d52fcf40b84))


### Bug Fixes

* 'set' object is not subscriptable ([b83aecd](https://github.com/gip-inclusion/le-marche/commit/b83aecd754e824249f84fec9c9367bfb436c91da))
* Amélioration de la commande 'create_content_pages' ([#1545](https://github.com/gip-inclusion/le-marche/issues/1545)) ([f4eefc8](https://github.com/gip-inclusion/le-marche/commit/f4eefc8e5f2c8ba479606de26e200703b8148e2c))
* Amélioration de la validation des champs url ([#1565](https://github.com/gip-inclusion/le-marche/issues/1565)) ([fb26956](https://github.com/gip-inclusion/le-marche/commit/fb2695650b97d312c104f00569f0b41f33bbf9d3))
* Autoriser seulement les "GET" sur PerimeterAutocompleteViewSet ([#1615](https://github.com/gip-inclusion/le-marche/issues/1615)) ([848df37](https://github.com/gip-inclusion/le-marche/commit/848df37fda048107621c3b30374833df1b1dd256))
* **Brevo:** AttributeError in 'api_brevo.create_contact' ([#1594](https://github.com/gip-inclusion/le-marche/issues/1594)) ([84c637c](https://github.com/gip-inclusion/le-marche/commit/84c637ccd0a31f3363ad06d8ee8a2bc362a9709e))
* **Brevo:** synchro des utilisateurs sans Tender ([#1592](https://github.com/gip-inclusion/le-marche/issues/1592)) ([1c8be5f](https://github.com/gip-inclusion/le-marche/commit/1c8be5f4f3b8398af6d77ec0c0ee76f2f9ae6460))
* **Brevo:** update_enabled arg in 'api_brevo.create_contact' ([#1593](https://github.com/gip-inclusion/le-marche/issues/1593)) ([b7b1c04](https://github.com/gip-inclusion/le-marche/commit/b7b1c0465c7f38b4224cef6712a15fc87294fc47))
* Condition invalide pour échapper le CSRF ([#1616](https://github.com/gip-inclusion/le-marche/issues/1616)) ([d35c21d](https://github.com/gip-inclusion/le-marche/commit/d35c21d3a0527d3cb54cd837b6b88800b15d6931))
* Erreurs de serialisation des inbound email ([#1619](https://github.com/gip-inclusion/le-marche/issues/1619)) ([987b044](https://github.com/gip-inclusion/le-marche/commit/987b04484948484015c564b9d795ce60383829ae))
* **Import des emplois:** exclusion du type OPCS de l'import ([#1603](https://github.com/gip-inclusion/le-marche/issues/1603)) ([67a64ab](https://github.com/gip-inclusion/le-marche/commit/67a64ab509dd0cd14188f84d0ecc42f27361dc32))
* **Liste des dépôts de besoin:** Correction d'une erreur javascript pour éviter un bug sur la liste ([#1574](https://github.com/gip-inclusion/le-marche/issues/1574)) ([8532546](https://github.com/gip-inclusion/le-marche/commit/8532546557dbb81db1445403a0c8004bafee8434))
* Migration de l'authentification de token vers un middleware + Sauvegarde des anciennes clés d'apis ([#1531](https://github.com/gip-inclusion/le-marche/issues/1531)) ([f37debf](https://github.com/gip-inclusion/le-marche/commit/f37debf5b8d1e43c3caa4095343ce6f046c1e27b))
* Remove dependabot auto pr action ([#1612](https://github.com/gip-inclusion/le-marche/issues/1612)) ([9925bcd](https://github.com/gip-inclusion/le-marche/commit/9925bcd6c10f526e4796f46032b3f4078de4028e))
* **Secteurs d'activités:** Mise à jour du calcul du nombre de secteurs pour le déduire des activités associées ([#1564](https://github.com/gip-inclusion/le-marche/issues/1564)) ([7ab2f2a](https://github.com/gip-inclusion/le-marche/commit/7ab2f2aee14b91a84dd2d02906bf03e7e98c668c))
* sectors_list_string replace by sector_groups_list_string on siae model ([0a27eca](https://github.com/gip-inclusion/le-marche/commit/0a27eca8492249916e4c634755566c6f608a6409))

## [2024.7.0](https://github.com/gip-inclusion/le-marche/compare/v2024.6.0...v2024.7.0) (2024-11-21)


### Features

* **Activités des structures:** Adaptation de l'affichage des secteurs d'activités des structures ([#1517](https://github.com/gip-inclusion/le-marche/issues/1517)) ([fa792d0](https://github.com/gip-inclusion/le-marche/commit/fa792d02a1a1de128cdedc408c3a5c64670b0c2d))
* **Activités des structures:** Adaptation de la recherche des Siaes ([#1519](https://github.com/gip-inclusion/le-marche/issues/1519)) ([b3a57e8](https://github.com/gip-inclusion/le-marche/commit/b3a57e8cdd997468f62b9955a18995b220d1a6df))
* **Activités des structures:** Remplacement de l'onglet "Votre référencement" ([#1505](https://github.com/gip-inclusion/le-marche/issues/1505)) ([273a11b](https://github.com/gip-inclusion/le-marche/commit/273a11b865cdc32149063178ea7dfcc2bdbf81a2))
* Ajout d'attributs de contact pour les acheteurs inscrits ([#1468](https://github.com/gip-inclusion/le-marche/issues/1468)) ([e508900](https://github.com/gip-inclusion/le-marche/commit/e5089008f713531b01b925cbafb3d4fbc03f68a6))
* Ajout d'un sitemap ([#1450](https://github.com/gip-inclusion/le-marche/issues/1450)) ([6895348](https://github.com/gip-inclusion/le-marche/commit/68953481080dbc63aaa9e4cab47d10ef779c357a))
* **Besoin:** Ajout d'un template de mail transactionnel quand le besoin est suivi par un partenaire commercial ([#1533](https://github.com/gip-inclusion/le-marche/issues/1533)) ([4939bf0](https://github.com/gip-inclusion/le-marche/commit/4939bf02a559177897eb539ec752e57f6d1f11ac))


### Bug Fixes

* **Activités des structures:** ajout de la correspondance directe sur la ville, le département ou la région de la structure ([#1487](https://github.com/gip-inclusion/le-marche/issues/1487)) ([21e97c4](https://github.com/gip-inclusion/le-marche/commit/21e97c428214e73c419e5ad0182cc19b2ace9636))
* **Activités des structures:** Correction de l'affichage des fiches structures sans type de prestation ([#1532](https://github.com/gip-inclusion/le-marche/issues/1532)) ([810669e](https://github.com/gip-inclusion/le-marche/commit/810669e19048b4a8c0d533c6eb9b19865e0cc509))
* Affichage du détail du dépôt de besoin ([#1515](https://github.com/gip-inclusion/le-marche/issues/1515)) ([b0b3a70](https://github.com/gip-inclusion/le-marche/commit/b0b3a706517442676fce76f2a18ff864fdfb3f12))
* Correction au niveau des logos d'entête ([#1538](https://github.com/gip-inclusion/le-marche/issues/1538)) ([443dc3f](https://github.com/gip-inclusion/le-marche/commit/443dc3fd086971803e75dab7afb8ce28921b179c))

## [2024.6.0](https://github.com/gip-inclusion/le-marche/compare/v2024.5.0...v2024.6.0) (2024-10-31)


### Features

* **Activités des structures:** Ajout du choix du périmètre d'intervention aux niveaux des activités ([#1457](https://github.com/gip-inclusion/le-marche/issues/1457)) ([8dc6f66](https://github.com/gip-inclusion/le-marche/commit/8dc6f662abac378d3ee11ce1e886eb17ad383708))
* **Activités des structures:** Déplacement du matching sur les activités ([#1464](https://github.com/gip-inclusion/le-marche/issues/1464)) ([b197675](https://github.com/gip-inclusion/le-marche/commit/b197675a0cf8e639fb7a69193e6c97a1e292c20e))
* Ajout d'un attribut pour filtrer l'envoi des besoins d'achat ([#1446](https://github.com/gip-inclusion/le-marche/issues/1446)) ([d074709](https://github.com/gip-inclusion/le-marche/commit/d07470904981fc4fdfaddcd811130a9faf1ece94))


### Bug Fixes

* **Activités des structures:** Adaptation de la commande de reprise de stock pour créer les activités ([#1476](https://github.com/gip-inclusion/le-marche/issues/1476)) ([9f497e6](https://github.com/gip-inclusion/le-marche/commit/9f497e6ad52282b16512adc295810ce5058a70e1))
* **Activités des structures:** Ajustement des exceptions de la commande de reprise de stock pour créer les activités ([#1480](https://github.com/gip-inclusion/le-marche/issues/1480)) ([b823940](https://github.com/gip-inclusion/le-marche/commit/b8239402ddf64555d0d671b4e02a2f3214220b5a))
* **Admin:** autoriser la suppression des SiaeUserRequest & TemplateTransactionalSendLog ([#1424](https://github.com/gip-inclusion/le-marche/issues/1424)) ([c64e984](https://github.com/gip-inclusion/le-marche/commit/c64e9848f2f4b47199178589dfc6b5ef181345bb))
* **Admin:** Correction de la mise en page des cases à cochées ([#1466](https://github.com/gip-inclusion/le-marche/issues/1466)) ([02fdbd5](https://github.com/gip-inclusion/le-marche/commit/02fdbd5e7704de5bb2ab7e244be2a85d8d149122))
* ajout des marges manquante en bas de page ([#1439](https://github.com/gip-inclusion/le-marche/issues/1439)) ([e2c4783](https://github.com/gip-inclusion/le-marche/commit/e2c478377315001d70a1f124023cc9a57780228f))
* Correction de l'affichage des cases à cocher des secteurs d'activités ([#1467](https://github.com/gip-inclusion/le-marche/issues/1467)) ([a06e89a](https://github.com/gip-inclusion/le-marche/commit/a06e89a73f308cdeaaeb6c549707ef65a94f6157))
* **Dashboard Acheteurs:** correction d'un onglet et des multiselects ([#1465](https://github.com/gip-inclusion/le-marche/issues/1465)) ([71cb6cd](https://github.com/gip-inclusion/le-marche/commit/71cb6cd311e88a49423058b34c6fb67be6008227))
* **Emails:** Template Transactional: remove result() call ([#1379](https://github.com/gip-inclusion/le-marche/issues/1379)) ([1809f5c](https://github.com/gip-inclusion/le-marche/commit/1809f5cb102042d13eb8284aa0493f6e3a29b6ee))
* **Entreprises:** ajuste le script de rattachement des utilisateurs en fonction de leur email (ajoute un @) ([#1406](https://github.com/gip-inclusion/le-marche/issues/1406)) ([daebacf](https://github.com/gip-inclusion/le-marche/commit/daebacf126a644b99cd2247677002f388fc78a17))
* fix dsfr des champs géré via AutoCompleteAccessible ([#1481](https://github.com/gip-inclusion/le-marche/issues/1481)) ([6107675](https://github.com/gip-inclusion/le-marche/commit/6107675f79154d0bf412b90d099313f4b81529ee))
* mini fixs SEO de la page faq  ([#1351](https://github.com/gip-inclusion/le-marche/issues/1351)) ([f527985](https://github.com/gip-inclusion/le-marche/commit/f52798508fa2a15c1eddedc09afc0374090b9c3c))
* **Recherche:** Les champs multiselect ne doivent pas s'activer lorsqu'ils sont désactivés ([#1440](https://github.com/gip-inclusion/le-marche/issues/1440)) ([ba0b379](https://github.com/gip-inclusion/le-marche/commit/ba0b379dcdf87a981db9dc7ef466bdfa5c656538))
* Réparation du montant lors de la synchro avec Brevo ([#1470](https://github.com/gip-inclusion/le-marche/issues/1470)) ([94e0680](https://github.com/gip-inclusion/le-marche/commit/94e068013416cdda176ca8c3dc05c0df17bacfb9))
* s3 storage fix in prod ([5a258a3](https://github.com/gip-inclusion/le-marche/commit/5a258a30f013fd1ebd96799a57525139558661fe))

## [2024.5.0](https://github.com/gip-inclusion/le-marche/compare/v2024.4.0...v2024.5.0) (2024-07-18)


### Features

* **cms:** ajout de page de FAQ sur le cms ([#1342](https://github.com/gip-inclusion/le-marche/issues/1342)) ([9aaa614](https://github.com/gip-inclusion/le-marche/commit/9aaa6140ee7e46f7c10d7c6750671da4520d7b5e))
* **Dépôt de besoins:** Ajout d'attributs pour le nouveaux process de suivi vip ([#1325](https://github.com/gip-inclusion/le-marche/issues/1325)) ([9fb6b62](https://github.com/gip-inclusion/le-marche/commit/9fb6b62132e030f27031720731415e04243913b3))
* **Emails:** avoir les logs d'envois des TemplateTransactional ([#1337](https://github.com/gip-inclusion/le-marche/issues/1337)) ([3addac3](https://github.com/gip-inclusion/le-marche/commit/3addac3deb5cf5fa3e8d59120a98447db8f70d31))
* **Emails:** Besoins : configurer les envois d'e-mails "avez-vous transactionné ?" avec TemplateTransactional (3/X) ([#1343](https://github.com/gip-inclusion/le-marche/issues/1343)) ([fe3bb3b](https://github.com/gip-inclusion/le-marche/commit/fe3bb3bc9e2f34d2c7a4832dccac54d51eac62e4))
* **Emails:** Besoins : configurer les envois d'e-mails à l'auteur avec TemplateTransactional (2/X) ([#1341](https://github.com/gip-inclusion/le-marche/issues/1341)) ([c02db9f](https://github.com/gip-inclusion/le-marche/commit/c02db9ff717131db83b5a31f06d693f266833613))


### Bug Fixes

* add class to fix faq button ([#1346](https://github.com/gip-inclusion/le-marche/issues/1346)) ([6d48f7f](https://github.com/gip-inclusion/le-marche/commit/6d48f7fc427cf8b2a9745a2366057c57d5a63f77))
* extra email variable refactoring. ref [#1337](https://github.com/gip-inclusion/le-marche/issues/1337) ([5a1ae57](https://github.com/gip-inclusion/le-marche/commit/5a1ae5780f2278e544e658645b78b8c8a191cfa8))

## [2024.4.0](https://github.com/gip-inclusion/le-marche/compare/v2024.3.0...v2024.4.0) (2024-07-03)


### Features

* ajout d'un attribut id sur les liens du bandeau pour suivre l'usage ([#1168](https://github.com/gip-inclusion/le-marche/issues/1168)) ([9f37452](https://github.com/gip-inclusion/le-marche/commit/9f37452f24e2573a45643d91e41d8e26fa5b2f82))
* Ajout d'un bandeau pour inciter les structures à visiter leur page d'accueil ([#1157](https://github.com/gip-inclusion/le-marche/issues/1157)) ([3d29098](https://github.com/gip-inclusion/le-marche/commit/3d29098d118f8be8b7db6e04f1299337f4134971))
* API pour le service Datacube ([#1160](https://github.com/gip-inclusion/le-marche/issues/1160)) ([24868e4](https://github.com/gip-inclusion/le-marche/commit/24868e49502bac5f3d17d0790c53323cbd9d614d))
* **Besoins:** changement de couleur des badgets des besoins clôturés ([#1247](https://github.com/gip-inclusion/le-marche/issues/1247)) ([ba48bc0](https://github.com/gip-inclusion/le-marche/commit/ba48bc0fd6f1a7478afb5c1d28afd19109f0fdb8))
* **Besoins:** Formulaire : allège les restrictions sur le champ "lien externe" ([#1163](https://github.com/gip-inclusion/le-marche/issues/1163)) ([18cdc1a](https://github.com/gip-inclusion/le-marche/commit/18cdc1af4232141795611c0e37fdd1025086273b))
* **Besoins:** Formulaire : si un lien externe est fourni, alors forcer le choix de réponse ([#1164](https://github.com/gip-inclusion/le-marche/issues/1164)) ([df05d51](https://github.com/gip-inclusion/le-marche/commit/df05d517bcc6e85d08eb238261c531693820e592))
* **Besoins:** gérer le numéro de téléphone de contact avec une librairie dédiée (v2) ([#1224](https://github.com/gip-inclusion/le-marche/issues/1224)) ([5df4a2d](https://github.com/gip-inclusion/le-marche/commit/5df4a2d7bc9b8a741d5626e1e2d1cb961134000e))
* **Besoins:** Mise à jour de la deuxième question pour la mesure d'impact ([#1296](https://github.com/gip-inclusion/le-marche/issues/1296)) ([0e8c240](https://github.com/gip-inclusion/le-marche/commit/0e8c2409001a21a4c0361a6f90b7479264c8b394))
* **Besoins:** Ordonner les besoins par date de publication ([#1243](https://github.com/gip-inclusion/le-marche/issues/1243)) ([aa0d005](https://github.com/gip-inclusion/le-marche/commit/aa0d00591260bf9ab7ec336aea1f2aeeb59625d4))
* **Brevo:** à l'inscription d'un utilisateur Structure, ajouter à une liste ([#1210](https://github.com/gip-inclusion/le-marche/issues/1210)) ([a91a735](https://github.com/gip-inclusion/le-marche/commit/a91a735d52df18d345e8f8e510eae3fd54f81088))
* **Brevo:** lorsqu'un utilisateur se rattache à une structure, envoyer l'info à Brevo ([#1211](https://github.com/gip-inclusion/le-marche/issues/1211)) ([f685d73](https://github.com/gip-inclusion/le-marche/commit/f685d73547686ae90f4750335922b6b7dc5943e0))
* **Brevo:** méthode pour lier des Contacts (User) à une Company (Siae) ([#1209](https://github.com/gip-inclusion/le-marche/issues/1209)) ([1aa7b99](https://github.com/gip-inclusion/le-marche/commit/1aa7b99fbd0e712d8c302ed10e8c8b0c03c8af2b))
* Changement du nom du lien d'inscription sur l'accueil des structures ([#1156](https://github.com/gip-inclusion/le-marche/issues/1156)) ([f65fcfa](https://github.com/gip-inclusion/le-marche/commit/f65fcfabf065f170a555150360576c3ef1eaaf5b))
* Changer url de la page "Auditer vos achats" ([#1218](https://github.com/gip-inclusion/le-marche/issues/1218)) ([3aaa04f](https://github.com/gip-inclusion/le-marche/commit/3aaa04fda6122869efd63c10dfacdaa4b27e9de3))
* **cms:** modification cms du nombre de home page ([365fe91](https://github.com/gip-inclusion/le-marche/commit/365fe916b87a46519a79cac8f1686072c24dad32))
* **crm:** Management commande de Synchronisation des utilisateurs avec Brevo ([#1178](https://github.com/gip-inclusion/le-marche/issues/1178)) ([c4733e7](https://github.com/gip-inclusion/le-marche/commit/c4733e77711d4b54d64500c455b66b511b3268dc))
* **DDB:** ajout d'un fragement wagtail pour info bulle des structures ([#1213](https://github.com/gip-inclusion/le-marche/issues/1213)) ([8a5151c](https://github.com/gip-inclusion/le-marche/commit/8a5151c7e5fa07fe52b53558e46fbdf1e89434ee))
* **dépôt de besoins:** Ajout des dépôts de besoins sur Brevo (1/3) ([#1123](https://github.com/gip-inclusion/le-marche/issues/1123)) ([5825776](https://github.com/gip-inclusion/le-marche/commit/58257761209d1816d5eefe22e3f7af8e2232823c))
* **Dépôt de besoins:** envoi d'un email à l'auteur d'un dépôt de besoin avec 5 ESI ([#1167](https://github.com/gip-inclusion/le-marche/issues/1167)) ([3775153](https://github.com/gip-inclusion/le-marche/commit/3775153f6f480dfdc7c20eb3b737b135213a650c))
* **Dépôt de besoins:** renommer les titres d'emails pour ne pas avoir l'impression d'envoyer deux fois le même mail ([#1166](https://github.com/gip-inclusion/le-marche/issues/1166)) ([f8f3d6c](https://github.com/gip-inclusion/le-marche/commit/f8f3d6ce5bd90ffb0a5e4e732e8aadaa3809fcee))
* **Dépôts de besoins:** Synchroniser les DDB avec brevo à la validation  ([#1179](https://github.com/gip-inclusion/le-marche/issues/1179)) ([b1495bf](https://github.com/gip-inclusion/le-marche/commit/b1495bf6f86694e2b350dfb567ab588af7a08db9))
* Dynamisation du lien en bas du mail des tops ESI à l'auteur d'un besoin ([#1170](https://github.com/gip-inclusion/le-marche/issues/1170)) ([d5ac41c](https://github.com/gip-inclusion/le-marche/commit/d5ac41c1bcb7c9833c089bdf436e6c355afae2e1))
* **Emails:** Besoins : configurer les envois d'e-mails avec TemplateTransactional ([#1193](https://github.com/gip-inclusion/le-marche/issues/1193)) ([d04efcb](https://github.com/gip-inclusion/le-marche/commit/d04efcbb33f6951e2b8c5b73b7716d6e5c369c4a))
* **Emails:** pouvoir envoyer les e-mails transactionnels depuis TemplateTransactional ([#1034](https://github.com/gip-inclusion/le-marche/issues/1034)) ([6836178](https://github.com/gip-inclusion/le-marche/commit/683617823749a3df3a8f56147ee6cb9c4e6b913c))
* **Emails:** remplacer l'envoi de finalisation du compte par son TemplateTransactional ([#1019](https://github.com/gip-inclusion/le-marche/issues/1019)) ([8db0c7f](https://github.com/gip-inclusion/le-marche/commit/8db0c7fb6836bc82d2a46e31969b91f8da657bd6))
* **Emails:** Structures : configurer les envois d'e-mails avec TemplateTransactional ([#1189](https://github.com/gip-inclusion/le-marche/issues/1189)) ([cf7201e](https://github.com/gip-inclusion/le-marche/commit/cf7201ed0b27108724bb60c6f2e77478fc9dd025))
* **Entreprises:** commande interactive pour créer de nouvelles entreprises à partir des infos des acheteurs ([#1165](https://github.com/gip-inclusion/le-marche/issues/1165)) ([e7c80af](https://github.com/gip-inclusion/le-marche/commit/e7c80af14aea3950866a9ae885ee8aec6477534f))
* **Home:** La page d'accueil d'un utilisateur d'une structure doit être celle dédiée aux ESI ([#1172](https://github.com/gip-inclusion/le-marche/issues/1172)) ([f2e75d6](https://github.com/gip-inclusion/le-marche/commit/f2e75d6b313fc78d69f18d57fe5515019dc99006))
* **inscription:** Lien direct vers la page des CGU sur le formulaire d’inscription ([#1262](https://github.com/gip-inclusion/le-marche/issues/1262)) ([6d1a7a6](https://github.com/gip-inclusion/le-marche/commit/6d1a7a61fd143e2a2cf187a7685093356743c7e9))
* **SIAE:** script d'import des ESATs du fichier csv Gesat/Handeco ([#1216](https://github.com/gip-inclusion/le-marche/issues/1216)) ([bfb1d28](https://github.com/gip-inclusion/le-marche/commit/bfb1d28527fbad470a61a19078e74d59414c034f))
* **SIAE:** script d'import/mise à jour des SEP ([#1231](https://github.com/gip-inclusion/le-marche/issues/1231)) ([fb50bc1](https://github.com/gip-inclusion/le-marche/commit/fb50bc1a4de72cf2c40a36bfa30f76be528ab977))
* statistiques sur la validité des numéros de téléphone ([#1219](https://github.com/gip-inclusion/le-marche/issues/1219)) ([8279dab](https://github.com/gip-inclusion/le-marche/commit/8279dabfafb2f29cadcff19b84150b3c0cb03632))
* **Structures:** gérer le numéro de téléphone de contact avec une librairie dédiée ([#1221](https://github.com/gip-inclusion/le-marche/issues/1221)) ([4856276](https://github.com/gip-inclusion/le-marche/commit/4856276125a140dd7abe22fcd400036c5790a960))
* **Structures:** historique de modification grâce à django-simple-history ([#1255](https://github.com/gip-inclusion/le-marche/issues/1255)) ([146ade4](https://github.com/gip-inclusion/le-marche/commit/146ade4ec50f969fddae8710576a5044c793c51c))
* **Structures:** nouveau champ pour stocker le brevo_company_id ([#1208](https://github.com/gip-inclusion/le-marche/issues/1208)) ([046818f](https://github.com/gip-inclusion/le-marche/commit/046818f29d59d8e99306b73df63a2e6fd0d2516e))
* **Structures:** Nouveau modèle SiaeActivity ([#1261](https://github.com/gip-inclusion/le-marche/issues/1261)) ([e458851](https://github.com/gip-inclusion/le-marche/commit/e45885119af12a5af20ef22fdcfd2a0099a00f95))
* **Structures:** pouvoir modifier une activité ([#1290](https://github.com/gip-inclusion/le-marche/issues/1290)) ([af22ef4](https://github.com/gip-inclusion/le-marche/commit/af22ef4da6c661a036d07435b4252b9e1f5c520a))
* **Structures:** Réindexation automatique des structures dans l'index Elasticsearch ([#1245](https://github.com/gip-inclusion/le-marche/issues/1245)) ([ac3de01](https://github.com/gip-inclusion/le-marche/commit/ac3de01cc5175e20bed53ac65f680592a900b6c3))
* **Structures:** SiaeActivity : afficher les activités dans la fiche ([#1308](https://github.com/gip-inclusion/le-marche/issues/1308)) ([0c02ab9](https://github.com/gip-inclusion/le-marche/commit/0c02ab9ba019882a32ff3da3d562ccf78d06cbee))
* **Structures:** SiaeActivity : commencer à afficher les activités dans un nouvel onglet du formulaire ([#1266](https://github.com/gip-inclusion/le-marche/issues/1266)) ([59c5707](https://github.com/gip-inclusion/le-marche/commit/59c5707766a36dee2e50d227a0f81eb7159b57ab))
* **Structures:** SiaeActivity : formulaire pour créer une nouvelle activité ([#1278](https://github.com/gip-inclusion/le-marche/issues/1278)) ([c68edcb](https://github.com/gip-inclusion/le-marche/commit/c68edcbdce1630f1c4ada3737e75d1a52738f924))
* **Structures:** SiaeActivity : pouvoir supprimer une activité ([#1277](https://github.com/gip-inclusion/le-marche/issues/1277)) ([c65ff19](https://github.com/gip-inclusion/le-marche/commit/c65ff19046cef229d5d6d143179f45c8cbcf759e))
* suppression de la limite du nombre de page d'accueil ([#1194](https://github.com/gip-inclusion/le-marche/issues/1194)) ([7fb1759](https://github.com/gip-inclusion/le-marche/commit/7fb175995a2e4399da30db19417aade81ddbdc02))
* **Utilisateurs:** gérer le numéro de téléphone avec une librairie dédiée ([#1215](https://github.com/gip-inclusion/le-marche/issues/1215)) ([fab59b8](https://github.com/gip-inclusion/le-marche/commit/fab59b8bc94e1735ad014699e9989363568e86ef))


### Bug Fixes

* add try/catch & tests on phone display. ref [#1234](https://github.com/gip-inclusion/le-marche/issues/1234) ([cf6401c](https://github.com/gip-inclusion/le-marche/commit/cf6401cebd146f9ad697ae6d925770d087c41d88))
* **API QPV:** Adaptation suite à la suppression du champs "code_qv" ([#1316](https://github.com/gip-inclusion/le-marche/issues/1316)) ([017afcf](https://github.com/gip-inclusion/le-marche/commit/017afcfeae081ccb27c5a013ef9933dfb3ea92f5))
* **Besoins:** Admin : filtre vraiment la liste des utilisateurs sur les bizdev ([#1242](https://github.com/gip-inclusion/le-marche/issues/1242)) ([8a46774](https://github.com/gip-inclusion/le-marche/commit/8a467745ba47ef64bff38f51a942fd6513c350e7))
* **Besoins:** Admin : restreindre la liste des admins affichés (bizdev only). ref [#1242](https://github.com/gip-inclusion/le-marche/issues/1242) ([a58e122](https://github.com/gip-inclusion/le-marche/commit/a58e122dc4902b2d5e64e5edc1487e347a027d45))
* **Besoins:** améliore la définition d'un besoin non dépassé ([#1176](https://github.com/gip-inclusion/le-marche/issues/1176)) ([617704e](https://github.com/gip-inclusion/le-marche/commit/617704ea1a7be2c6f1b771f8a9f87f6bb245151b))
* **Besoins:** arrête l'envoi par batch lorsque la date de clotûre du besoin est dépassée ([#1175](https://github.com/gip-inclusion/le-marche/issues/1175)) ([bf1a8ff](https://github.com/gip-inclusion/le-marche/commit/bf1a8ff0f070bd2f5132bffaca858879ce56f71d))
* **Besoins:** évite d'envoyer des mails de relance aux structures pas intéressées ([#1158](https://github.com/gip-inclusion/le-marche/issues/1158)) ([ffd6704](https://github.com/gip-inclusion/le-marche/commit/ffd6704a91b6f5e789cb8a28429d8e3d4792ef03))
* **Besoins:** ne pas autoriser le ré-envoi si la date de clôture est dépassée ([#1177](https://github.com/gip-inclusion/le-marche/issues/1177)) ([780245b](https://github.com/gip-inclusion/le-marche/commit/780245bd94509f29c24fced2e4aca4e3d61f435a))
* **Besoins:** réduit le nombre de mails de relances envoyés aux structures concernées ([#1161](https://github.com/gip-inclusion/le-marche/issues/1161)) ([7a56950](https://github.com/gip-inclusion/le-marche/commit/7a56950aab732873557228dea114cea40475dc9d))
* **Brevo:** Admin : afficher les identifiants (contact_id, deal_id, company_id) ([#1228](https://github.com/gip-inclusion/le-marche/issues/1228)) ([90eaaed](https://github.com/gip-inclusion/le-marche/commit/90eaaed926040eb0332ba4946b3eb7341a005386))
* **Brevo:** Améliorer le script de synchro des structures vers Brevo ([#1229](https://github.com/gip-inclusion/le-marche/issues/1229)) ([76b35c3](https://github.com/gip-inclusion/le-marche/commit/76b35c3bed83731bc7634866bd160a51bb05fb66))
* **Brevo:** Mieux gérer la mises à jour des contacts Brevo (et envoyer le téléphone) ([#1230](https://github.com/gip-inclusion/le-marche/issues/1230)) ([539d00f](https://github.com/gip-inclusion/le-marche/commit/539d00f45270f78ac93d097b1532566f406a4a3c))
* **Brevo:** mieux gérer le rattachement des contact avec leur company / deal ([#1212](https://github.com/gip-inclusion/le-marche/issues/1212)) ([1daf3b8](https://github.com/gip-inclusion/le-marche/commit/1daf3b85f8747e3a5d9b14cb593e6915f4dbf3a9))
* **ci:** Typo dans la config auto-assign-reviewers. ref [#1265](https://github.com/gip-inclusion/le-marche/issues/1265) ([608a2b8](https://github.com/gip-inclusion/le-marche/commit/608a2b84ef81cd0020b35f37831a5a14eeb0313d))
* **Contact:** fix de l'url sur la page de contact ([30120b2](https://github.com/gip-inclusion/le-marche/commit/30120b25f405f83b6e45155b1eb734b7baddd6c9))
* correction typo du badge super prestataire ([2c84271](https://github.com/gip-inclusion/le-marche/commit/2c84271e1958155b624ca4b735ff2556f63e1993))
* **Emails:** ajout de valeur par défaut pour subject ([#1205](https://github.com/gip-inclusion/le-marche/issues/1205)) ([59f2497](https://github.com/gip-inclusion/le-marche/commit/59f249736c913ab50796e7acf1fbb286de3db85e))
* **Emails:** ajout de valeurs par défaut pour from_email & from_name ([#1204](https://github.com/gip-inclusion/le-marche/issues/1204)) ([ad2bbc0](https://github.com/gip-inclusion/le-marche/commit/ad2bbc09e99ca243d17c08e0ea0fdf796d9bd873))
* Fix du nom et prénom dans la synchronisation des contacts avec Brevo ([#1311](https://github.com/gip-inclusion/le-marche/issues/1311)) ([e7c1ef5](https://github.com/gip-inclusion/le-marche/commit/e7c1ef5a475928a9bdc63438878eb6ee621ac989))
* forgot last contact_phone_display. ref [#1234](https://github.com/gip-inclusion/le-marche/issues/1234) ([f88fd90](https://github.com/gip-inclusion/le-marche/commit/f88fd90a8250601ffffa480ed0bd21f766ed9a45))
* **History:** update requirements.txt. ref [#1255](https://github.com/gip-inclusion/le-marche/issues/1255) ([3d79ce1](https://github.com/gip-inclusion/le-marche/commit/3d79ce1dc31d6f06263281e3b377fea987fa350d))
* **Hubspot:** Répare la création de contact (suite au changement de format du numéro de téléphone) ([#1232](https://github.com/gip-inclusion/le-marche/issues/1232)) ([bdfd7a1](https://github.com/gip-inclusion/le-marche/commit/bdfd7a1754e3561a940d0a9ef97aedc129ea7260))
* **import:** Correction sur l'import des numéros de téléphone  ([#1237](https://github.com/gip-inclusion/le-marche/issues/1237)) ([b352489](https://github.com/gip-inclusion/le-marche/commit/b352489ce1cb0546ccc0748fdb01cb87ec06bff7))
* Répare l'affichage des numéros de téléphone (suite au changement de format) ([#1234](https://github.com/gip-inclusion/le-marche/issues/1234)) ([ae7d6e2](https://github.com/gip-inclusion/le-marche/commit/ae7d6e2fd38c1ef10070481fd580f2756679b581))
* **Session:** Stockage des sessions côté serveur ([#1270](https://github.com/gip-inclusion/le-marche/issues/1270)) ([bc51057](https://github.com/gip-inclusion/le-marche/commit/bc510575b00ece58f0a4120657f0acbb9b3454ea))
* **Signup:** Rendre l'année dynamique dans le questionnaire pour les acheteurs lors de l'inscription ([#1284](https://github.com/gip-inclusion/le-marche/issues/1284)) ([561d689](https://github.com/gip-inclusion/le-marche/commit/561d689b1f4e536ee77804048ee0b0978e40ac16))
* **Structures:** afficher seulement aux admins l'information que la structure n'est pas encore inscrite ([#1239](https://github.com/gip-inclusion/le-marche/issues/1239)) ([e26c47b](https://github.com/gip-inclusion/le-marche/commit/e26c47bc96fe7bdc1f25859b0693bf1381c2166c))
* **Structures:** Détail : améliorer les informations affichées aux admin ([#1238](https://github.com/gip-inclusion/le-marche/issues/1238)) ([73dd4d9](https://github.com/gip-inclusion/le-marche/commit/73dd4d9d3f9cfc52ac437c35efe848f86e7db001))
* **Structures:** fix refactoring array to string functions. ref [#1267](https://github.com/gip-inclusion/le-marche/issues/1267) ([224ec11](https://github.com/gip-inclusion/le-marche/commit/224ec117594b3aa6519fd460e0fa892e59146825))
* **Structures:** quelques améliorations d'affichage sur la page recherche & détails ([#1240](https://github.com/gip-inclusion/le-marche/issues/1240)) ([20ee3d1](https://github.com/gip-inclusion/le-marche/commit/20ee3d1f67107d818296e15dbef607138275a0c9))
* Uniformisation de la hauteur des blocs du carousel ([#1223](https://github.com/gip-inclusion/le-marche/issues/1223)) ([ec96cb6](https://github.com/gip-inclusion/le-marche/commit/ec96cb674978477426eb4000da9b5d11a0989585))
* **wagtail:** add csrf trusted origins to fix wagtail preview ([#1276](https://github.com/gip-inclusion/le-marche/issues/1276)) ([1d31350](https://github.com/gip-inclusion/le-marche/commit/1d31350175996d7a38943fc090a056a54293d7f9))

## [2024.3.0](https://github.com/gip-inclusion/le-marche/compare/v2024.2.0...v2024.3.0) (2024-04-08)


### Features

* **Besoins:** Admin: afficher les utilisateurs qui ont vu le besoin ([#1151](https://github.com/gip-inclusion/le-marche/issues/1151)) ([a543999](https://github.com/gip-inclusion/le-marche/commit/a543999f36579e6e78ccd370360cc81b9e397656))
* **Besoins:** Filtre par type de structure dans le ciblage des structures par recherche sémantique ([#1152](https://github.com/gip-inclusion/le-marche/issues/1152)) ([d3a0e1a](https://github.com/gip-inclusion/le-marche/commit/d3a0e1ae725af7d8a70e5942502f02e1a672bd33))
* **Besoins:** mettre à jour l'utilisateur de la mise en relation ([#1144](https://github.com/gip-inclusion/le-marche/issues/1144)) ([0adc957](https://github.com/gip-inclusion/le-marche/commit/0adc957c4c25883cb175b380b35e78443f71327a))
* **Besoins:** pouvoir rattacher un utilisateur à une mise en relation ([#1143](https://github.com/gip-inclusion/le-marche/issues/1143)) ([a4e2f1f](https://github.com/gip-inclusion/le-marche/commit/a4e2f1f766adaae1de271816f5c2fe38f9ee0dd2))
* **Besoins:** Sondage transaction : ajouter une option "Pas encore" ([#1154](https://github.com/gip-inclusion/le-marche/issues/1154)) ([bf8a23d](https://github.com/gip-inclusion/le-marche/commit/bf8a23dfcdbffd794822493bc69de6383af4a9cb))
* **Brevo:** après une recherche d'un acheteur, ajouter à une liste Brevo ([#1135](https://github.com/gip-inclusion/le-marche/issues/1135)) ([ec146dc](https://github.com/gip-inclusion/le-marche/commit/ec146dc199856b7a7644ad5f4f1e174a82e271ec))
* **Home:** Rendre les sections de l'accueil davantage modifiable ([#1141](https://github.com/gip-inclusion/le-marche/issues/1141)) ([551c39a](https://github.com/gip-inclusion/le-marche/commit/551c39ae45c079cca171c3fc30c9d0821f9643ec))


### Bug Fixes

* **Besoins:** répare l'ouverture au clic de 2 liens dfférents ([#1148](https://github.com/gip-inclusion/le-marche/issues/1148)) ([f8b741e](https://github.com/gip-inclusion/le-marche/commit/f8b741e6415e8f79c47ccea7c710d0d393d25209))
* erreur sur une variable non définie. ref [#1102](https://github.com/gip-inclusion/le-marche/issues/1102) ([ecadcd0](https://github.com/gip-inclusion/le-marche/commit/ecadcd011f0511cc36a2b1f042a68202ec4c27fc))
* L'image de la section Ecosystème ne change pas ([#1149](https://github.com/gip-inclusion/le-marche/issues/1149)) ([fe2ae2d](https://github.com/gip-inclusion/le-marche/commit/fe2ae2deb0012244a33ef284b91e4dc8c4c77a65))
* Répare des tests qui cassent parfois ([#1147](https://github.com/gip-inclusion/le-marche/issues/1147)) ([48fa4fe](https://github.com/gip-inclusion/le-marche/commit/48fa4fe9cb703d9e9760a3068521b9787829102a))
* Répare encore des tests qui cassent parfois ([#1155](https://github.com/gip-inclusion/le-marche/issues/1155)) ([84547bb](https://github.com/gip-inclusion/le-marche/commit/84547bbf1c61858f90a543e9741a5b9c09387da4))
* **Tracker:** errors linked to user_id ([e309d59](https://github.com/gip-inclusion/le-marche/commit/e309d598800acfb735cdf46b6b5016678d10f1f0))

## [2024.2.0](https://github.com/gip-inclusion/le-marche/compare/v2024.1.0...v2024.2.0) (2024-03-22)


### Features

* **admin_tenders:** Rediriger vers la section structures après la validation des DDB ([#1111](https://github.com/gip-inclusion/le-marche/issues/1111)) ([e29a3d4](https://github.com/gip-inclusion/le-marche/commit/e29a3d43b6291cab0bf9d965a7fe6ff1f1792647))
* **Admin:** Secteurs : afficher le nombre de besoins concernés ([#1118](https://github.com/gip-inclusion/le-marche/issues/1118)) ([8674309](https://github.com/gip-inclusion/le-marche/commit/8674309a229f30b657f2ae50f721b74889ea564d))
* **Besoins:** Admin : Avoir le status de la mise en relation ([#1121](https://github.com/gip-inclusion/le-marche/issues/1121)) ([9b5926c](https://github.com/gip-inclusion/le-marche/commit/9b5926c0aef4f950ad69760c9148436d1a2ed462))
* **Besoins:** Admin : Connaitre le nombre de besoins déposés par chaque entreprise ([#1120](https://github.com/gip-inclusion/le-marche/issues/1120)) ([9181d37](https://github.com/gip-inclusion/le-marche/commit/9181d37d7399c276b4c5ee50361b8c0d4017a7d3))
* **Besoins:** Admin : filtre de la liste par bizdev ([#1134](https://github.com/gip-inclusion/le-marche/issues/1134)) ([078b95a](https://github.com/gip-inclusion/le-marche/commit/078b95a40c5d91eeb690e2aee005ca125a618a52))
* **Besoins:** Admin: afficher la liste des structures intéressées ([#1131](https://github.com/gip-inclusion/le-marche/issues/1131)) ([9e801e9](https://github.com/gip-inclusion/le-marche/commit/9e801e92989e15809fa892a4bfa23bc774237ba1))
* **Besoins:** Admin: pouvoir indiquer quelle structure a effectivement transactionnée ([#1133](https://github.com/gip-inclusion/le-marche/issues/1133)) ([7438756](https://github.com/gip-inclusion/le-marche/commit/74387568638691c154cdbb83e99855b9b4fae6e8))
* **Besoins:** Ajout d'un filtre par type de besoin ([#1104](https://github.com/gip-inclusion/le-marche/issues/1104)) ([d2054a6](https://github.com/gip-inclusion/le-marche/commit/d2054a6eeb3cf41f4dd2919ee4f6f79e4a9358e0))
* **Besoins:** Ajout du nombre d'occurences en status Nouveau sur le filtre par type ([#1117](https://github.com/gip-inclusion/le-marche/issues/1117)) ([feaf563](https://github.com/gip-inclusion/le-marche/commit/feaf56369d5628fb6159f2c23bf10cb3c6600c46))
* **Besoins:** Connaitre la source de la transaction ([#1124](https://github.com/gip-inclusion/le-marche/issues/1124)) ([1e9539f](https://github.com/gip-inclusion/le-marche/commit/1e9539f05fa74b49e36003472cf9d7318b73510a))
* **Besoins:** Détail : afficher l'entreprise de l'acheteur en gras ([#1138](https://github.com/gip-inclusion/le-marche/issues/1138)) ([2d6c3ab](https://github.com/gip-inclusion/le-marche/commit/2d6c3abaeb47201af51657826153ca12e604fb7a))
* **Besoins:** Détail : mieux afficher l'email d'equipe ([#1137](https://github.com/gip-inclusion/le-marche/issues/1137)) ([f090cbc](https://github.com/gip-inclusion/le-marche/commit/f090cbcd6622371750c8f4490a751d9a38dea53e))
* **Besoins:** Détail : répare l'affichage de la modale d'inscription pour les utilisateurs inconnus ([#1136](https://github.com/gip-inclusion/le-marche/issues/1136)) ([666513f](https://github.com/gip-inclusion/le-marche/commit/666513f59213eaeeb2bcf2a5f63d772c5c94e40e))
* **Besoins:** Mesure du NPS des acheteurs ([#1119](https://github.com/gip-inclusion/le-marche/issues/1119)) ([82e3e14](https://github.com/gip-inclusion/le-marche/commit/82e3e14324186affa80f89e3c125b3d78493da74))
* **Besoins:** mettre à jour automatiquement la date de transaction ([#1122](https://github.com/gip-inclusion/le-marche/issues/1122)) ([4f502e7](https://github.com/gip-inclusion/le-marche/commit/4f502e7ea5a0237479ac2bbbd1d5c2020fe2be67))
* **Besoins:** Nouveau champ M2M 'admins' pour aider le suivi ([#1113](https://github.com/gip-inclusion/le-marche/issues/1113)) ([e042239](https://github.com/gip-inclusion/le-marche/commit/e0422390f0663172bd277904cef3f21dfddf12f2))
* **Besoins:** nouveau champ pour stocker la date de transaction ([#1116](https://github.com/gip-inclusion/le-marche/issues/1116)) ([7c52702](https://github.com/gip-inclusion/le-marche/commit/7c52702edd097471ca48d956f178d872d40631d5))
* **Besoins:** Permettre à une structure contactée de décliner dès l'e-mail ([#1114](https://github.com/gip-inclusion/le-marche/issues/1114)) ([fe8ec03](https://github.com/gip-inclusion/le-marche/commit/fe8ec0300aa41908ad6cd221a63c6bf0d52ba5c6))
* **Besoins:** Sondage transaction : mettre à jour le TenderSiae en fonction de la réponse ([#1139](https://github.com/gip-inclusion/le-marche/issues/1139)) ([2e358ba](https://github.com/gip-inclusion/le-marche/commit/2e358baa725ee721d5d8a4639cbf4b9c733c34c9))
* **Brevo:** Commande pour synchroniser toutes les semaines les entreprises (SIAE) ([#1106](https://github.com/gip-inclusion/le-marche/issues/1106)) ([5880917](https://github.com/gip-inclusion/le-marche/commit/5880917b59815a94252435745b88b22024d5b955))
* **Brevo:** méthode pour créer (et maj) des entreprises (SIAE) ([#1099](https://github.com/gip-inclusion/le-marche/issues/1099)) ([1225a0c](https://github.com/gip-inclusion/le-marche/commit/1225a0cad121df3eb6c26b037e121da5c4c8acb0))
* **Dashboard SIAE:** Réordonner les besoins (derniers publiés en premier) ([#1098](https://github.com/gip-inclusion/le-marche/issues/1098)) ([df3fd2f](https://github.com/gip-inclusion/le-marche/commit/df3fd2f3523007f732ed965b825ba02542b9a6fc))
* **Dépôt de besoins:** Permettre aux structures de supprimer les dépôts de besoins expirés ([#1110](https://github.com/gip-inclusion/le-marche/issues/1110)) ([4404359](https://github.com/gip-inclusion/le-marche/commit/4404359a26bdaa3312660becc270df649a25a08a))
* **Entreprises:** nouveau champ pour stocker le nombre d'acheteurs sur LinkedIn ([#1140](https://github.com/gip-inclusion/le-marche/issues/1140)) ([1fd1fc3](https://github.com/gip-inclusion/le-marche/commit/1fd1fc379c375e747fa213a1cc60242aa6de18ef))
* **Entreprises:** nouveau champ user_tender_count, nouvelle commande pour mettre les count à jour ([#1132](https://github.com/gip-inclusion/le-marche/issues/1132)) ([a58f4af](https://github.com/gip-inclusion/le-marche/commit/a58f4af6191ca8e0fba5a096e61249df7c585d61))
* **SIAE:** nouveau champ 'extra_data' ([#1105](https://github.com/gip-inclusion/le-marche/issues/1105)) ([047a321](https://github.com/gip-inclusion/le-marche/commit/047a321c5547334ab75c2bf17b6d4607001ba8d8))
* **SIAE:** nouvelle property is_live ([#1107](https://github.com/gip-inclusion/le-marche/issues/1107)) ([019cac8](https://github.com/gip-inclusion/le-marche/commit/019cac8bd9531a5a952150c6a1011e224c211447))
* **SIAE:** script pour aider le rattachement à leur réseau (grâce à des import csv) ([#1109](https://github.com/gip-inclusion/le-marche/issues/1109)) ([464cde5](https://github.com/gip-inclusion/le-marche/commit/464cde563d3aa1c75e3788e0f92f35bf994a1e3b))


### Bug Fixes

* **Admin:** Besoins : répare le filtre par montant exact ([#1112](https://github.com/gip-inclusion/le-marche/issues/1112)) ([31208bb](https://github.com/gip-inclusion/le-marche/commit/31208bba82c0d7ae9f3976e656aa0db6ae8c9e6b))
* **Admin:** Besoins: ajuste les règles de filtrage pour le montant exact. ref [#1112](https://github.com/gip-inclusion/le-marche/issues/1112) ([fa21009](https://github.com/gip-inclusion/le-marche/commit/fa210093091f17b4bb392d42b77dd1df5749da87))
* Affichage du header droit de la liste des dépôt de besoins ([#1128](https://github.com/gip-inclusion/le-marche/issues/1128)) ([df3b452](https://github.com/gip-inclusion/le-marche/commit/df3b452c9260df54c44d45c482abf752f8d917a4))
* **API:** Exclure les structures OPCS des résultats ([#1129](https://github.com/gip-inclusion/le-marche/issues/1129)) ([b79133e](https://github.com/gip-inclusion/le-marche/commit/b79133e49f202073e0db13d203aa5d43ed33afd2))
* **API:** mise à jour du lien vers api.gouv ([#1127](https://github.com/gip-inclusion/le-marche/issues/1127)) ([b95885d](https://github.com/gip-inclusion/le-marche/commit/b95885d40134e24d2dc08a2b167a3697893df4e0))
* **APProch:** Améliore le wording du bouton CTA des besoins provenant d'APProch. ref [#923](https://github.com/gip-inclusion/le-marche/issues/923) ([9844546](https://github.com/gip-inclusion/le-marche/commit/9844546b49fa530beb4eedb20d74046a36c55601))
* **Besoins:** Correction sur le nombre d'occurrences en status Nouveau sur le filtre par type ([#1126](https://github.com/gip-inclusion/le-marche/issues/1126)) ([6bc052b](https://github.com/gip-inclusion/le-marche/commit/6bc052b5d1608b587a350c92cad4338f97ee4d00))
* **Besoins:** Exclure les structures OPCS du matching ([#1130](https://github.com/gip-inclusion/le-marche/issues/1130)) ([b0fb1c9](https://github.com/gip-inclusion/le-marche/commit/b0fb1c91bda4ad4a11a464b13dc6c9cfd45e0cbd))
* **CI:** affiche mieux les diff dans le script de déploiement. ref [#1063](https://github.com/gip-inclusion/le-marche/issues/1063) ([6f014b3](https://github.com/gip-inclusion/le-marche/commit/6f014b301fa3e8fc667b805718203866e19fc30a))
* **Dépôt de besoin:** Réparation du badge de clôture ([#1125](https://github.com/gip-inclusion/le-marche/issues/1125)) ([af0bd82](https://github.com/gip-inclusion/le-marche/commit/af0bd823965a5a15f48c461415e0412d8e640385))
* on TenderSiae survey_transaction answer, only update Tender if True. ref [#1124](https://github.com/gip-inclusion/le-marche/issues/1124) ([14c2e05](https://github.com/gip-inclusion/le-marche/commit/14c2e05436fb194a348f74a6575a3bd6db97109f))
* **SIAE:** Evite que le champ is_delisted soit écrasé à chaque synchro avec les emplois ([#1108](https://github.com/gip-inclusion/le-marche/issues/1108)) ([57a6093](https://github.com/gip-inclusion/le-marche/commit/57a60939cffd28b1f06d41eadfa6c685130429ec))

## [2024.1.0](https://github.com/gip-inclusion/le-marche/compare/v2023.12.29...v2024.1.0) (2024-02-23)

- fix(tender): Suppression de l'affichage du badge "Nouveau" sur les DDB clôturés (#1088)
- feat(besoins): Sondage aux prestataires intéressés : cron & task (#1085)
- refactor: améliore un peu la génération des URL absolute & admin (#1100)
- refactor(tender): Admin : ré-ajoute les stats du nombre de structures qui ont vues et qui ont cliquées (#1101)
- refactor: retrait de l'envoi de mail à j+2 aux auteurs de besoins incrémentaux (#1094)
- feat(Admin): Ajout d'un filtre pour retrouver les dépôts de besoins incrémentaux (#1090)
- feat(besoins): méthode pour dupliquer un besoin (#1097)
- feat(contact): Ajout de MTCaptcha sur le formulaire de contact (#1096)
- refactor(tender): Réorganisation des colonnes de la liste des dépôts de besoins dans l'admin (#1091)
- fix(dashboard_siae): fix du bug d'affichage des tabs pour compléter les données des siaes (#1093)
- feat(tender): Admin : réduire la taille de la page grâce aux collapse (#1089)
- ci: ajout d'une Github Action qui vérifie le nommage des PR (respect de la norme "conventional commits") (#1078)
- ci: ajout de la Github Action "release-please" (#1077)
- fix(siae): répare la génération des Siae.kind constants (#1087)
- Refonte ergonomique de la liste des opportunités (#1079)
- Ajout du survol sur les Super ESI (#1083)
- Dépôt de besoins : ETQ Admin, je veux gérer les notifications des partenaires et groupements (#1084)
- [Affichage des Siaes] Ajout du badge visuel des super esi (#1068)
- Dépôts de besoins (API) : Ajout de champs dans le but d'optimiser le travail des bizdevs (#1082)
- refactor(api): Mieux renvoyer les structures dans l'endpoint par siret (#1081)
- api(siae): ajoute le parent dans l'endpoint siae kinds (#1075)
- refactor(siae): réorganise un peu les kind constants (#1076)
- feat(api) Pouvoir chercher les structures par SIREN (#1074)
- Ouverture de la recherche par mot clé (#1073)
- Dépôt de besoin : sondage aux prestataires : formulaire et vue (#1072)
- Dépôt de besoin : stocker les (futurs) résultats du sondage "avez-vous transactionné ?" envoyé aux structures (#1071)
- [API] Cleanup (retirer inbound parsing de la doc) (#1067)
- Dépôt de besoin x APProch : si besoin existant, mais kind a changé, alors en re-créer un (#1070)
- [CMS] Ajout de pages "privée" de wagtails (#1054)
- Dépôt de besoin x APProch : si besoin existant, mettre à jour certains champs (#1069)
- Dépôt de besoin : prestataires intéressés : répare le filtrage (#1066)
- DevOps : Script de déploiement : voir les diffs ajoutées (#1063)
- Dépôt de besoin : certains auteurs de besoins ne veulent plus recevoir d'e-mails (#1064)
- [Dépôt de besoin] Conserver les coordonnées dans les données d'étape (#1059)
- Dépôt de besoin : envoi sondage transaction : mise en place de relances (#1057)
- Dépôt de besoin x APProch : stocker l'ID lorsqu'un nouveau besoin est reçu via l'API (#1062)
- Dépôt de besoin x APProch : nouveaux champs pour stocker leur ID (#1058)
- [Dépôt de besoin] Ciblage des structures par recherche sémantique (#1053)
- Dépôt de besoin : Détail : cacher les CTA en fonction de l'intérêt en co-traitance du prestataire (#1055)
- Dépôt de besoin : détail : template pour le message affiché aux utilisateurs SIAE sans structures (#1060)
- Dépôt de besoin : Détail : basculer l'action 'pas intéressé' dans une modale (#1056)
- Dépôt de besoin : Détail : cacher les CTA en fonction de l'intérêt ou non du prestataire (#1050)
- Dépôt de besoin : Détail : fix un bug sur les besoins anonymes (#1051)
- Dépôt de besoin : Détail : Template dédié à la sidebar (#1048)
- Recherche sémantique avec elasticsearch (#988)
- Dépôt de besoin : fini de réparer l'envoi par batch (#1047)
- Dépôt de besoin : Répare le trop grand nombre d'envoi d'e-mails en mode batch (#1046)
- Dépôt de besoin : pouvoir indiquer la raison du non intérêt (#1045)
- Tech : workflow Github pour auto-assigner l'auteur à sa PR (#1042)
- Tech : cleanup des tests pour utiliser au maximum assertTrue / False / IsNone / IsNotNone (#1041)
- Dépôt de besoin : quelques améliorations (fixtures, icon) (#1040)
- Dépôt de besoin : mise à jour des stats suite à l'ajout de cocontracting & not_interested (#1039)
- Dépôt de besoin : permettre à une structure d'indiquer qu'elle n'est pas intéressée (#1038)
- Emails : finaliser la configuration d'envoi d'-mails transactionnels avec Brevo (#1033)
- Emails : ajout des contacts à la liste des acheteurs sur Brevo (#1028)
- Dépôt de besoin : nouveau champ pour stocker l'info des structures pas intéréssées (#1037)
- [Wagtail] Correction du chargement des pages statiques (#1035)
- Emails : ajout de quelques champs de configuration de l'e-mail dans les templates (#1024)
- Mise à jour de la version de Django (4.2.9) (#1032)
- Feature(Conversations): Suppression des données de prise de contacts après 6 mois (#1027)
- feat(dépôt de besoins) : Admin : filtre par type du client (#1029)

## 2023.12.29

- Feature(Dépôt de besoin) : Envoi des dépôt de besoins par lot (#1025)
- Permettre aux acheteurs de voir les prestataires ouverts à la co-traitance (#1021)
- [Admin] Correction du formulaire d'édition des structures qui est parfois tronqué
- Emails : nouveau modèle TemplateTransactional pour stocker nos configurations (#1018)
- Dépôt de besoins : envoyer les e-mails aux prestataires (et aux partenaires) à partir d'une autre adresse mail (#1020)
- [Dépôt de besoin] Répare les horaires du cron d'envoi des besoins validés (#1017)
- [Utilisateurs] Inscription : évite la valeur par défaut pour buyer_kind_detail (#1016)
- [Utilisateurs] Rattacher correctement les utilisateurs provenant de Tally (#1010)
- [Inbound Parsing] Améliorer la visibilité des disclaimer (#1015)
- Permettre de renseigner le montant exact sur l'api des dépôt de besoins(#1014)
- [Tech] Envoyer certaines notifications Slack vers le canal #support (#1013)
- [Structures] Mettre à jour régulièrement la valeur de super_badge (#1009)
- [Structures] Nouveau champ super_badge et méthode pour le calculer (#1008)
- [Tech] Modifier le canal par défaut d'envoi des notifications Slack (#1012)
- [Dépôt de besoin] Inversement de l'ordre des boutons pour gérer l'appui de la touche Entrée
- [Dépôt de besoin] Admin : ajout de validation sur les règles de ciblage par km (#1011)
- [Tech] Léger refactoring des champs en lecture seule dans l'admin (#1004)
- [Structures] Stats supplémentaires pour Metabase (#1003)
- [Utilisateurs] nouveau type "Particulier" (#1002)
- [Dépôt de besoin] Envoyer en asynchrone les besoins validés (#998)
- [Dépôt de besoin] Nouveau status "SENT" (#997)
- Mise à jour du logo pour les réseaux sociaux  (#1005)
- [Tech] Rajoute 2 notifications Slack sur des commandes cron (#1001)
- [Dépôt de besoin] Ciblage par rayon en KM (#999)
- [Tech] Renommer le script de synchro avec le C1 (#996)
- [Structures] Réparer la synchro avec les emplois (#993)
- Mise à jours des données enregistrées dans l'inbound parsing (#985)
- [Structures] Nouveau champ pour stocker le taux de complétion de la fiche (#991)
- [Structures] Rattachement : déplacer la mention de contacter le support (#992)
- [Documentation] info sur le setup de pre-commit (#972)
- [Utilisateurs] Inscription : demander aux acheteurs leur type d'organisation (#987)
- [Dépôt de besoin] Modifications dans la tâche d'envoi du sondage transaction (#986)

## 2023.11.24

- [Tech] Refactoring des constants (#984)
- [Utilisateurs] Renommer les choix des types d'acheteurs (#983)
- fix filter_with_tender too complex error. ref #975
- [Dépôt de besoin] Fix du bug de périmètre et France entière (#975)
- [Dépôt de besoin] Stats : ajout de tests supplémentaires pour les utilisateurs avec plusieurs structures (#978)
- [Structures] Admin : réorganiser les colonnes (#982)
- [Dépôt de besoin] Renommer "Devis" en "Demande de devis" (#981)
- [Tracker] Petites améliorations sur siae_kind & user_kind (#980)
- [Entreprises] Tâche pour rattacher automatiquement les utilisateurs tous les lundi (#979)
- [Dépôt de besoin] Renvoyer une erreur 404 si le besoin n'est pas trouvé (#977)
- Update Github repo URL (migration from betagouv to gip-inclusion) (#976)
- Fix du bug de téléchargement des structures qui ont vu des dépôts de besoins (#969)
- [Structures] Rattachement : répare le lien vers les contact à la fin du workflow (#974)
- [Dépôt de besoin] Renommer les noms des templates  (#973)
- [Dépôt de besoin] Dans les e-mails aux prestataires, envoyer aussi le montant (#967)
- Export : ajouter la property Siae.kind_parent (#962)
- Affichage des dépôts de besoins de type sourcing et anonyme côté utilisateur (#961)
- Ajout des secteurs d'activité dans le profile des acheteurs (#963)
- Permettre aux utilisateurs de publier un DDB en anonyme (#956)
- fix questions list on csrf (#971)
- Suppression d'un message de log inutile (#970)
- Another tender survey form wording improvement (label, placeholder). ref #964
- [Dépôt de besoin] Admin : réparer les stats des structures (#968)
- [Tableau de bord] Se rattacher à une structure : clarifier le wording (#966)
- [Calculateur] Impact social : clarifier le wording (#965)
- Small wording change on tender transaction email. ref #964
- [Dépôt de besoin] Champ supplémentaires dans le sondage transaction (#964)

## 2023.10.27

- Structure : nouvelle property "kind_parent" (#955)
- Fiche : ajout MTM sur le bouton Annuaire Entreprise (#954)
- Admin : améliore le rendu des checkbox sur mobile (#953)
- Label : pouvoir uploader un label dans l'admin (#946)
- [Dépôt de besoin] Stats supplémentaires pour Metabase (#939)
- Dépôt de besoin : envoyer les notif Slack dans un canal dédié (#957)
- Refactoring : remplacer datetime par timezone (#952)
- Refactoring : clarifier si une stat vient d'une annotation (#949)
- Fix du nom de l'entreprise d'un dépôt de besoin (#945)
- Mise à jours de la date de dernière activité des structures  (#930)
- Suppression de Hotjar (#950)
- Import des ESATs du fichier Excel de l'ASP (#948)
- [Dépôt de besoin] Répare l'affichage (ou pas) du montant (#944)
- [Dépôt de besoin] Inverser l'affichage des secteurs et de l'entreprise (#943)
- [Dépôt de besoin] Afficher seulement 3 secteurs d'activité max (#942)
- [Dépôt de besoin] Conservation des données des dépôts abandonnés (#938)
- [Structure] Afficher le nombre d'établissement dans la fiche (#941)
- [Structure] Calculer le nombre d'établissements (#940)
- [Dépot de besoin] Correction de la mise en forme la description (#937)
- [Dépot de besoin] Correction sur la forme de la description (#936)
- [Dépot de besoin] Possibilité de mettre en forme la description (#934)
- [Fiche structure] Répare l'affichage de la carte si Inbound désactivé (#928)
- [Dépôt de besoin] Faire un encart dédié aux informations admin (#926)
- [Dépôt de besoin] Ajouter une stat du nombre de structures qui ont cliqué OU vu (#927)

## 2023.09.29

- [Dépôt de besoin] : Déplacement des champs "description" et "date de clôture" (#924)
- [Dépôt de besoin] Rajouter un message pour les besoins en provenance d'APProch (#923)
- [Dépôt de besoin] Sondage J+30 : mettre à jour siae_transactioned (#922)
- [CMS- Homepage] Correction sur l'affichage des logos partenaires
- [Dépôt de besoin] Permettre aux admin d'indiquer que le besoin n'a PAS transactionné (#920)
- [Dépôt de besoin] Simplification du formulaire en supprimant les informations de contact pour les utilisateurs connectés (#916)
- [Recherche] Répare les liens de redirection après la modale de recherche avancée (#919)
- [Fiche structure] Faire un encart dédié aux informations admin (#918)
- [Aperçu du besoin] Ajout du bouton "Répondre en co-traitance" (#914)
- [Dépôt de besoin - dashboard acheteur] ajout d'une vue pour voir les structures qui ont vu le DB (#912)
- [Fiche structure] Intégrer la carte et les informations géo (#915)
- [Recherche] Remonter les prestataires qui ont un logo (#913)
- add images with links (#906)
- Recherche : enlever les inscriptions des acheteurs aux listes Mailjet  (#911)
- [Dépôt de besoin] Simplification du formulaire (#909)
- Inbound parsing : améliorer le matching (#910)
- Dépôt de besoin : réduire le taux d'abandon à la dernière étape (aperçu) (#907)
- Improve API tests. ref #905
- Dépôt de besoin : permettre à certains utilisateurs anonyme de se mettre en relation (#899)
- Dépôt de besoin : nouveau champ pour overrider le company_name affiché (#905)
- Fiche structure : changer le label des salariés en insertion pour les ESAT/EA (#903)
- Fiche structure : indiquer la forme juridique (#902)
- [Inbound Parsing] Modification du format d'email (#901)
- MTCaptcha : tracer l'erreur uniquement si l'utilisateur n'est pas en cause - Round 2
- Dépôt de besoin : stocker la date d'envoi du sondage J+30 (#895)
- Tarteaucitron : ajout de Google Tag Manager (#896)
- [Inbound parsing] Validation par l'admin du premier e-mail de la conversation (#894)
- Refactoring : séparer Dashboard & Siaes (#892)
- Fix forgot to move tests in new dashboard_networks app. ref #867
- set company name in mail signature instread siae (#890)
- Dépôt de besoin : Admin : filtre "montant renseigné ?" (#891)
- [Inbound parsing] Ajouter de l’identité du client et disclaimer dans le premier mail (#889)
- Ajout d'un lien dans l'entête avec le nombre de demandes reçues à lire (#881)
- Refactoring : renommer certaines views (#884)
- Remplacement du terme "mail" par "e-mail"
- Script de maj des dépendances : rendre poetry update optionnel (#879)
- Dépôt de besoin : utiliser django-sesame pour générer les liens du sondage J+30 (#880)
- [CI] Mise à jour de la Github action de mise en cache des dépendances
- change wording on contact card v2

## 2023.08.25

### Ajouté

- Recherche / Fiche
    - Admin : Affichage des conversations d'une structure (#863)
    - Inbound parsing : Ajout du nom et prénom au formulaire de contact des structures (#858)
    - Inbound parsing : Ajout d'un formulaire de contact (#843)
    - Inbound parsing : Enregistrer les records d'inbound parsing (#842)
- Dépôt de besoin
    - envoyer un e-mail à J+30 aux auteurs pour savoir si il y a eu une transaction (#865)
    - CTA sur les fiches structures (#864)
    - Admin : possibilité d'ajuster l’incrémentalité d'un besoin (#859)
    - stocker les résultats du sondage J+30 (#873)
- Home
    - Nouveau champ User.favorite_list_count pour éviter des requêtes (#870)
- Tech
    - captcha : log error only if the user is not responsible (#868)
    - Initialiser l'Email inbound Parsing (#840)

### Modifié

- Recherche / Fiche
    - Inbound parsing : améliorer l'affichage admin (#866)
    - Inbound parsing : Migrer vers ShortUUIDField (#854)
    - Inbound parsing : Mise à jour des infos pratique des structures (#861)
    - Inbound parsing : fix sender for the first message (#878)
    - Inbound parsing : fix serializer for incoming data. ref #842
    - Inbound parsing : jout de MTCaptcha sur le formulaire de contact des structures (#862)
    - Inbound parsing : utiliser send_mail au lieu de EmailMultiAlternatives (#857)
    - Inbound parsing : améliorer l'affichage dans l'admin (#856)
    - display pretty messages of conversation (#855)
    - fix html display. ref #854
    - Fix: Affichage du nombre d'employées en insertion par structure (#877)
- Dépôt de besoin
    - Partenaires besoins : admin : pouvoir chercher par e-mail (#852)
    - Partenaires besoins : pouvoir indiquer des notes dans l'admin (#851)
- Home
    - Footer : répare le lien vers les mentions légales (#872)
- Tech
    - fix geo perimeter flacky test (#869, #876)
    - Refactoring : séparer Dashboard & Networks (#867)
    - Dépendances : mettre à jour le repo pointant vers raphodn (#860)
    - Admin : répare l'affichage des vues avec fieldset (#823)
    - Affichage des erreurs dans les tests, même en parallèle (#853)
    - Suppression des requêtes N+1 sur la recherche de partenaires (#874)
    - Fiche structure : petite optimisation de la queryset (#875)

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
    - Hotfix: remove unused perimeters_autocomplete_field.js (#800)
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
    - add siae_kind to TenderSerializer. ref #695
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
    - Synchronisation avec le C1 : rajouté le champ `brand` à la liste des champs synchronisés
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
