<!--
  Sync Impact Report
  ===================
  Version change: 1.0.1 → 1.1.0
  Modified sections:
    - Lean & Simple First: prioritize reuse of existing code (lib/, skills)
    - Lisibilité inter-équipes: centralized glossary for domain jargon
    - Development Workflow: removed type checking, added codebase consistency rule
  Templates requiring updates:
    - spec template: update glossary reference approach
    - All other templates: review for alignment with reuse-first principle
-->

# Constitution Autometa

## Principes fondamentaux

### I. Lean & Simple First

Chaque fonctionnalité DOIT commencer par l'implémentation viable la plus simple.
Pas d'abstraction prématurée, pas de généralisation spéculative, pas d'infrastructure
qui ne répond pas à un besoin immédiat et validé.

- Réutiliser le code existant (`lib/`, skills, utilitaires) avant d'écrire du nouveau code.
  Commencer par un script ou module à usage unique uniquement si aucun composant existant
  ne couvre le besoin.
- YAGNI s'applique inconditionnellement : construire pour les besoins d'aujourd'hui,
  pas pour des besoins hypothétiques futurs.
- La préparation au passage à l'échelle signifie des interfaces propres et un design
  stateless, PAS une infrastructure pré-construite pour une charge qui n'existe pas encore.
- La complexité DOIT être justifiée dans la table de suivi de complexité du plan.

### II. Sécurité par conception

La sécurité est une contrainte non-négociable à chaque étape — conception, code,
déploiement, exploitation. Ce projet traite des données de l'État français et DOIT
respecter l'état de l'art en matière de sécurité dans les domaines IA, web et cloud.

- **OWASP Top 10** : chaque spec et implémentation DOIT traiter les risques OWASP
  pertinents (injection, authentification cassée, SSRF, etc.).
- **Risques spécifiques à l'IA** : les sorties des modèles DOIVENT être traitées comme
  des entrées non fiables. L'injection de prompt, l'empoisonnement de données et les
  vecteurs d'extraction de modèle DOIVENT être évalués dans le modèle de menaces de
  chaque spec.
- **Sécurité cloud** : les secrets DOIVENT utiliser des variables d'environnement ou un
  coffre-fort, jamais commités dans le code source. L'exposition réseau DOIT suivre le
  principe du moindre privilège. Toute communication externe DOIT utiliser TLS.
- **Chaîne d'approvisionnement** : les dépendances DOIVENT être épinglées et auditées.
  Aucune dépendance transitive avec des CVE critiques connues.
- **Protection des données** : le traitement des DCP DOIT être conforme au RGPD.
  La minimisation des données s'applique — ne collecter que le strict nécessaire.

### III. Open Source & Transparence

Ce projet est public. Chaque décision, artefact et processus DOIT être
compréhensible et auditable par quiconque.

- Le code, les specs et les plans sont publiés sous licence open source.
- Pas de sécurité par l'obscurité : la protection repose sur des contrôles
  appropriés, pas sur une implémentation cachée.
- Les décisions DOIVENT être documentées dans les specs et plans avec leur justification.
- Les identifiants sensibles et secrets opérationnels sont les SEULES exceptions
  à la transparence totale.

### IV. Impact mesurable

Chaque fonctionnalité DOIT définir comment son succès et son impact seront mesurés
avant le début de l'implémentation.

- Chaque spec DOIT inclure des critères de succès quantitatifs liés aux résultats
  utilisateur (pas seulement des métriques techniques).
- La mesure d'impact DOIT couvrir : l'adoption (volume d'utilisation), l'efficacité
  (complétion des tâches, taux d'erreur) et l'efficience (temps gagné, coût réduit).
- Les valeurs de référence DOIVENT être établies avant le lancement ; la mesure
  post-lancement DOIT être planifiée.
- Si une métrique ne peut pas être mesurée avec l'instrumentation existante, la spec
  DOIT inclure l'instrumentation comme exigence.

### V. Lisibilité inter-équipes

Les specs sont des documents de travail pour les équipes produit, design, data et dev.
Elles DOIVENT être compréhensibles sans connaissances techniques spécialisées.

- Utiliser du français courant pour les descriptions, user stories et justifications.
- Les détails d'implémentation technique vont dans le plan, pas dans la spec.
- Le jargon métier DOIT être défini dans un glossaire centralisé unique.
  Les specs DOIVENT y renvoyer au lieu de redéfinir les termes.
- Chaque spec DOIT être structurée de sorte que tout membre d'équipe puisse la relire
  et proposer des modifications sans avoir besoin de lire le code source.

## Sections obligatoires des specs

Chaque spécification de fonctionnalité DOIT inclure, en plus des sections standard
du template :

### Modèle de menaces

Une section courte de modélisation des menaces couvrant :

1. **Actifs** : quelles données ou capacités cette fonctionnalité expose-t-elle ?
2. **Acteurs malveillants** : qui pourrait abuser de cette fonctionnalité (attaquants
   externes, utilisateurs malveillants, dépendances compromises) ?
3. **Vecteurs d'attaque** : quels sont les 3 à 5 scénarios d'attaque réalistes ?
4. **Atténuations** : quels contrôles répondent à chaque vecteur ?
5. **Risque résiduel** : quel risque subsiste après les atténuations, et est-il
   accepté ?

### Mesure d'impact

Une section détaillant :

1. **Métriques de succès** : indicateurs quantitatifs avec valeurs cibles.
2. **Valeur de référence** : état actuel avant la mise en production.
3. **Méthode de mesure** : comment et quand les métriques seront collectées.
4. **Cadence de revue** : quand l'équipe évaluera les résultats (ex. 30 jours
   après le lancement).

## Workflow de développement

- La revue de code est obligatoire pour tout changement.
- Chaque PR DOIT être limitée à un seul changement logique et dimensionnée pour
  une relecture facile. Les ajouts importants DOIVENT être découpés en PR
  incrémentales, fusionnables indépendamment.
- Chaque PR DOIT passer le linting et les tests avant fusion.
- Les changements sensibles en matière de sécurité (auth, accès aux données,
  exposition API) DOIVENT recevoir une revue de sécurité explicite.
- Le code DOIT rester cohérent avec le reste de la codebase : en partager le style,
  les choix architecturaux, réutiliser tout ce qui peut l'être et ne pas introduire
  de duplications ou de fonctionnements exceptionnels, sauf dûment justifié.
- Les dépendances DOIVENT être ajoutées via le gestionnaire de paquets avec des
  versions épinglées ; le vendoring manuel nécessite une justification.
- Le déploiement suit le principe du moindre privilège : permissions minimales,
  exposition réseau minimale, accès aux données minimal.

## Gouvernance

Cette constitution est la référence autoritaire pour les principes du projet.
Elle prévaut sur les orientations contradictoires d'autres documents.

- **Amendements** : nécessitent (1) une proposition écrite décrivant le changement
  et sa justification, (2) une relecture par au moins un membre de chaque équipe
  (produit, dev, data), (3) mise à jour de ce document avec incrément de version.
- **Versionnement** : suit le versionnement sémantique — MAJEUR pour les suppressions
  de principes ou redéfinitions incompatibles, MINEUR pour les nouveaux principes ou
  expansions matérielles, PATCH pour les clarifications et corrections de formulation.
- **Revue de conformité** : chaque spec et plan DOIT inclure une section Vérification
  Constitution attestant l'alignement avec ces principes.
- **Résolution de conflits** : quand les principes entrent en conflit (ex. simplicité
  vs. sécurité), la sécurité l'emporte. Documenter le compromis dans la table de suivi
  de complexité du plan.

**Version** : 1.1.0 | **Ratifiée** : 2026-03-25 | **Dernier amendement** : 2026-03-27
