#!/bin/bash -l

# Update API ZRR fields for new siaes

# Do not run if this env var is not set:
if [[ -z "$CRON_UPDATE_COUNT_FIELDS_ENABLED" ]]; then
    echo "CRON_UPDATE_COUNT_FIELDS_ENABLED not set. Exiting..."
    exit 0
fi

# About clever cloud cronjobs:
# https://www.clever-cloud.com/doc/tools/crons/

if [[ "$INSTANCE_NUMBER" != "0" ]]; then
    echo "Instance number is ${INSTANCE_NUMBER}. Stop here."
    exit 0
fi

# $APP_HOME is set by default by clever cloud.
cd $APP_HOME

# django-admin update_count_fields
django-admin update_count_fields --fields etablissement_count