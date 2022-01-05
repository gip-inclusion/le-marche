#!/bin/bash -l

# Generate a list of all the Siae (XLS & CSV), and store on S3

# Do not run if this env var is not set:
if [[ -z "$CRON_SIAE_EXPORT_ENABLED" ]]; then
    echo "CRON_SIAE_EXPORT_ENABLED not set. Exiting..."
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

django-admin export_all_siae_to_file --format all
