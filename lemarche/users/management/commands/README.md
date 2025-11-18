# Commandes d'import d'utilisateurs

## Architecture

### Classe de base : `BaseImportUsersCommand`

La classe `BaseImportUsersCommand` fournit la logique commune pour toutes les commandes d'import :

- **Lecture du fichier CSV** avec gestion d'erreurs
- **Création/mise à jour d'utilisateurs** avec gestion des doublons
- **Envoi de liens de réinitialisation de mot de passe** pour les nouveaux utilisateurs
- **Hooks extensibles** pour les actions post-import

### Méthodes à implémenter

Les sous-classes doivent implémenter ces méthodes abstraites :

- `get_user_kind()` : Type d'utilisateur (ex: `User.KIND_BUYER`)
- `get_user_fields()` : Champs supplémentaires pour la création
- `get_update_fields()` : Champs à mettre à jour pour les utilisateurs existants

## Commandes disponibles

### Import d'acheteurs : `import_buyers`

```bash
python manage.py import_buyers fichier.csv template_code company_slug
```

**Paramètres :**

- `fichier.csv` : Fichier CSV avec les acheteurs
- `company_slug` : Slug de l'entreprise
- `template_code` : Code template Brevo pour l'invitation

**Fonctionnalités spécifiques :**

- Rattachement à une entreprise
- Ajout à la liste Brevo
- Ajout du domaine email à l'entreprise

### Import de partenaires : `import_partners`

```bash
python manage.py import_partners fichier.csv template_code
```

**Paramètres :**

- `fichier.csv` : Fichier CSV avec les partenaires
- `template_code` : Code template Brevo pour l'invitation

**Fonctionnalités spécifiques :**

- Type de partenaire fixé à "Facilitateur"
- Pas de rattachement à une entreprise
- Pas d'ajout à Brevo

## Format CSV

Toutes les commandes utilisent le même format CSV avec ces en-têtes :

```csv
FIRST_NAME,LAST_NAME,EMAIL,PHONE,POSITION
Jean,Dupont,jean.dupont@example.com,0123456789,Directeur
Marie,Martin,marie.martin@example.com,0987654321,Responsable
```

## Exemples d'utilisation

### Import de partenaires facilitateurs

```bash
python manage.py import_partners fixtures/tests/partners_import.csv welcome_partners
```

### Import d'acheteurs pour une entreprise

```bash
python manage.py import_buyers acheteurs.csv ma-entreprise welcome_buyers
```

## Gestion des erreurs

- **Utilisateurs existants** : Mise à jour des champs spécifiques
- **Erreurs de validation** : Affichage dans les logs, traitement continu
- **Transactions** : Chaque utilisateur traité indépendamment

## Extensibilité

Pour créer une nouvelle commande d'import :

1. Hériter de `BaseImportUsersCommand`
2. Implémenter les méthodes abstraites
3. Ajouter des arguments spécifiques si nécessaire
4. Surcharger les hooks pour les actions post-import
