# Spécification de fonctionnalité : [NOM DE LA FONCTIONNALITÉ]

**Branche** : `[###-nom-feature]`
**Créée le** : [DATE]
**Statut** : Brouillon
**Entrée** : Description utilisateur : "$ARGUMENTS"

## Scénarios utilisateur & Tests *(obligatoire)*

<!--
  IMPORTANT : Les user stories doivent être PRIORISÉES en parcours utilisateur ordonnés par importance.
  Chaque user story/parcours doit être TESTABLE INDÉPENDAMMENT - c'est-à-dire que si vous n'en implémentez
  qu'UNE SEULE, vous devez obtenir un MVP (Produit Minimum Viable) qui apporte de la valeur.

  Attribuez des priorités (P1, P2, P3, etc.) à chaque story, P1 étant la plus critique.
  Considérez chaque story comme une tranche autonome de fonctionnalité pouvant être :
  - Développée indépendamment
  - Testée indépendamment
  - Déployée indépendamment
  - Démontrée aux utilisateurs indépendamment
-->

### User Story 1 - [Titre court] (Priorité : P1)

[Décrire ce parcours utilisateur en langage courant]

**Justification de la priorité** : [Expliquer la valeur et pourquoi ce niveau de priorité]

**Test indépendant** : [Décrire comment tester indépendamment — ex. « Peut être entièrement testé en [action spécifique] et apporte [valeur spécifique] »]

**Scénarios d'acceptation** :

1. **Étant donné** [état initial], **Quand** [action], **Alors** [résultat attendu]
2. **Étant donné** [état initial], **Quand** [action], **Alors** [résultat attendu]

---

### User Story 2 - [Titre court] (Priorité : P2)

[Décrire ce parcours utilisateur en langage courant]

**Justification de la priorité** : [Expliquer la valeur et pourquoi ce niveau de priorité]

**Test indépendant** : [Décrire comment tester indépendamment]

**Scénarios d'acceptation** :

1. **Étant donné** [état initial], **Quand** [action], **Alors** [résultat attendu]

---

### User Story 3 - [Titre court] (Priorité : P3)

[Décrire ce parcours utilisateur en langage courant]

**Justification de la priorité** : [Expliquer la valeur et pourquoi ce niveau de priorité]

**Test indépendant** : [Décrire comment tester indépendamment]

**Scénarios d'acceptation** :

1. **Étant donné** [état initial], **Quand** [action], **Alors** [résultat attendu]

---

[Ajouter d'autres user stories si nécessaire, chacune avec une priorité assignée]

### Cas limites

<!--
  ACTION REQUISE : Le contenu de cette section représente des exemples.
  Remplir avec les vrais cas limites.
-->

- Que se passe-t-il quand [condition aux limites] ?
- Comment le système gère-t-il [scénario d'erreur] ?

## Exigences *(obligatoire)*

<!--
  ACTION REQUISE : Le contenu de cette section représente des exemples.
  Remplir avec les vraies exigences fonctionnelles.
-->

### Exigences fonctionnelles

- **EF-001** : Le système DOIT [capacité spécifique, ex. « permettre aux utilisateurs de créer un compte »]
- **EF-002** : Le système DOIT [capacité spécifique, ex. « valider les adresses email »]
- **EF-003** : Les utilisateurs DOIVENT pouvoir [interaction clé, ex. « réinitialiser leur mot de passe »]
- **EF-004** : Le système DOIT [exigence données, ex. « persister les préférences utilisateur »]
- **EF-005** : Le système DOIT [comportement, ex. « journaliser tous les événements de sécurité »]

*Exemple de marquage d'exigences floues :*

- **EF-006** : Le système DOIT authentifier les utilisateurs via [À CLARIFIER : méthode d'auth non spécifiée — email/mot de passe, SSO, OAuth ?]
- **EF-007** : Le système DOIT conserver les données utilisateur pendant [À CLARIFIER : durée de rétention non spécifiée]

### Entités clés *(inclure si la fonctionnalité implique des données)*

- **[Entité 1]** : [Ce qu'elle représente, attributs clés sans implémentation]
- **[Entité 2]** : [Ce qu'elle représente, relations avec les autres entités]

## Modèle de menaces *(obligatoire — cf. constitution)*

<!--
  ACTION REQUISE : Chaque spec DOIT inclure un modèle de menaces.
  Rester concis — se concentrer sur les risques réalistes pour cette fonctionnalité spécifique.
-->

### Actifs

- [Quelles données ou capacités cette fonctionnalité expose-t-elle ?]

### Acteurs malveillants

- [Qui pourrait abuser de cette fonctionnalité ? Attaquants externes, utilisateurs malveillants, dépendances compromises ?]

### Vecteurs d'attaque & Atténuations

| # | Vecteur d'attaque | Probabilité | Impact | Atténuation |
|---|-------------------|-------------|--------|-------------|
| 1 | [ex. Injection SQL via champ de recherche] | [Haute/Moy/Basse] | [Haut/Moy/Bas] | [ex. Requêtes paramétrées] |
| 2 | [ex. Injection de prompt dans contenu généré par IA] | [Haute/Moy/Basse] | [Haut/Moy/Bas] | [ex. Assainissement des sorties] |
| 3 | [ex. SSRF via paramètre URL] | [Haute/Moy/Basse] | [Haut/Moy/Bas] | [ex. Liste blanche d'URLs] |

### Risque résiduel

- [Quel risque subsiste après les atténuations ? Est-il accepté ?]

## Critères de succès *(obligatoire)*

<!--
  ACTION REQUISE : Définir des critères de succès mesurables.
  Ils doivent être agnostiques technologiquement et mesurables.
-->

### Résultats mesurables

- **CS-001** : [Métrique mesurable, ex. « Les utilisateurs peuvent créer un compte en moins de 2 minutes »]
- **CS-002** : [Métrique mesurable, ex. « Le système supporte 1000 utilisateurs simultanés sans dégradation »]
- **CS-003** : [Métrique satisfaction, ex. « 90% des utilisateurs réussissent la tâche principale au premier essai »]
- **CS-004** : [Métrique métier, ex. « Réduire les tickets support liés à [X] de 50% »]

## Mesure d'impact *(obligatoire — cf. constitution)*

<!--
  ACTION REQUISE : Définir comment mesurer l'impact de cette fonctionnalité.
  Les valeurs de référence DOIVENT être établies avant le lancement.
-->

### Métriques de succès

| Métrique | Référence (actuel) | Cible | Méthode de mesure |
|----------|-------------------|-------|-------------------|
| [ex. Taux de complétion] | [ex. 65%] | [ex. 85%] | [ex. Suivi d'événements Matomo] |
| [ex. Temps pour compléter l'action] | [ex. 4 min] | [ex. 2 min] | [ex. Analyse de durée de session] |
| [ex. Taux d'adoption] | [ex. 0 utilisateurs] | [ex. 500 utilisateurs/mois] | [ex. Visiteurs uniques sur la page] |

### Cadence de revue

- [ex. Première revue : 30 jours après le lancement. Trimestrielle ensuite.]

## Hypothèses

<!--
  ACTION REQUISE : Le contenu de cette section représente des exemples.
  Remplir avec les vraies hypothèses basées sur des choix par défaut raisonnables
  quand la description de la fonctionnalité ne précisait pas certains détails.
-->

- [Hypothèse sur les utilisateurs cibles, ex. « Les utilisateurs ont une connexion internet stable »]
- [Hypothèse sur les limites du périmètre, ex. « Le support mobile est hors périmètre pour la v1 »]
- [Hypothèse sur les données/environnement, ex. « Le système d'authentification existant sera réutilisé »]
- [Dépendance à un système/service existant, ex. « Nécessite l'accès à l'API profil utilisateur existante »]
