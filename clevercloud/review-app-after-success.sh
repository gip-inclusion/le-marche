#!/bin/sh

###################################################################
###################### Review apps entrypoint #####################
###################################################################

# Skip this step when redeploying a review app.
if [ "$SKIP_FIXTURES" = true ] ; then
    echo "Skipping fixtures."
    exit
fi

echo "Loading perimeters"
./manage.py import_regions
./manage.py import_departements
# ./manage.py import_communes

echo "Loading fixtures"
# TODO
