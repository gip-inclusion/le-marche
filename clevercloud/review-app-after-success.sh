#!/bin/sh

# https://github.com/betagouv/itou/blob/master/clevercloud/review-app-after-success.sh

###################################################################
###################### Review apps entrypoint #####################
###################################################################

# Skip this step when redeploying a review app.
if [ "$SKIP_FIXTURES" = true ] ; then
    echo "Skipping fixtures."
    exit
fi

echo "Loading perimeters"
# django-admin import_regions
# django-admin import_departements
# django-admin import_communes
PGPASSWORD=$POSTGRESQL_ADDON_PASSWORD pg_restore -d $POSTGRESQL_ADDON_DB -h $POSTGRESQL_ADDON_HOST -p $POSTGRESQL_ADDON_PORT -U $POSTGRESQL_ADDON_USER --if-exists --clean --no-owner --no-privileges $APP_HOME/lemarche/perimeters/management/commands/data/perimeters_20220104.sql

# `ls $APP_HOME` does not work as the current user
# does not have execution rights on the $APP_HOME directory.
echo "Loading fixtures"
ls -d $APP_HOME/lemarche/fixtures/django/* | xargs django-admin loaddata
