# Migrer twig vers django
Le moteur de template Twig est très similaire à celui de Django (ainsi qu'à Jinja).

### Remarques
- L'organisation des fichiers et répertoires est repris de itou-cocorico

### Ce qui est identique
- les blocs `{% block machin %}{% endblock %}`
- les include (même les mots-clés genre `only`)
- l'intégration des variables `{{ une_variable }}`

### Des petites choses qui changent
- les commentaires twig style `{# HELLO WORLD ! #}` ne fonctionnent pas sous django
- la racine des fichiers change, là où Twig utilise le nom des apps `{% include '@MonApp' %}`, Django utilise le répertoire depuis la racine de `templates`
- extension de fichiers : twig utilise `.html.twig`, django simplement `.html`
- les opérateurs conditionnels (if, for, ...) peuvent varier, à voir au cas par cas

### Ce qui bloque
- Django ne connait pas la commande `{% embed %}` qui permet d'inclure un autre template tout en pouvant remplacer les blocks à la manière d'un `extend`. Ce n'est pas bloquant, mais il faut veiller à retirer les `embed` et revoir les `extend`, tout en veillant à ne pas écraser le noms des blocks.

## Liste des différences:

### Assets
Twig : `{{asset('favicon.ic')}}`
Django : `{% static "favicon.ico" %}`

### Webpack
Sous twig les assets sont gérés par webpack / encore.
L'intégration sous django est plus directe.

Twig : `{{ encore_entry_link_tags('itou_common') }}`
Django : `<link rel="stylesheet" href="{% static "css/itou.css" %}" type="text/css">`

### Scripts
Twig : `{% block javascripts %}`
Djang : `{% block scripts %}`
