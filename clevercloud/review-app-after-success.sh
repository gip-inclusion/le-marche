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
django-admin import_regions
django-admin import_departements
django-admin import_communes

# `ls $APP_HOME` does not work as the current user
# does not have execution rights on the $APP_HOME directory.
echo "Loading fixtures"
ls -d $APP_HOME/lemarche/fixtures/django/* | xargs django-admin loaddata
