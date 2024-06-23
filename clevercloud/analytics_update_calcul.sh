#!/bin/bash -l

# Calculate the historics fields

# Do not run if this env var is not set:
if [[ -z "$CRON_ANALYTICS_UPDATE_CALCUL" ]]; then
    echo "CRON_ANALYTICS_UPDATE_CALCUL not set. Exiting..."
    exit 0
fi

# About clever cloud cronjobs:
# https://developers.clever-cloud.com/doc/administrate/cron/

if [[ "$INSTANCE_NUMBER" != "0" ]]; then
    echo "Instance number is ${INSTANCE_NUMBER}. Stop here."
    exit 0
fi

# $APP_HOME is set by default by clever cloud.
cd $APP_HOME

django-admin collect_analytics_data --save
