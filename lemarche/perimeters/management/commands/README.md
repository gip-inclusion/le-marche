# Perimeter data

## Where does the data come from?

- Régions : https://geo.api.gouv.fr/regions
- Départements : https://geo.api.gouv.fr/departements
- Communes : https://geo.api.gouv.fr/communes

See the `generate_*.py` scripts to understand how we built the `data/*.json` files.

Note:
- some extra data is added during the import, see the `import_*.py` scripts
- there are 35000+ communes, import will take a bit of time

## How-to import

First make sure that there aren't any Perimeters in the database
```
> python manage.py shell

from lemarche.perimeters.models import Perimeter
from lemarche.utils.data import reset_app_sql_sequences

Perimeter.objects.count()
Perimeter.objects.all().delete()
reset_app_sql_sequences("perimeters")
```

Then run the import scripts
```
> python manage.py import_regions
> python manage.py import_departements
> python manage.py import_communes
```

## How-to export

If you wish to generate a .sql file of all the perimeters
```
> pg_dump -d itoumarcheapi --table=perimeters_perimeter --data-only --column-inserts --format=custom > data/perimeters.sql

// why --format=custom?
// because without, pg_restore will return an error: "input file appears to be a text format dump. Please use psql."
```
