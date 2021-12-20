#!/bin/bash -l

# Fetch new siaes from C1 + update existing

# Do not run if this env var is not set:
if [[ -z "$CRON_SYNC_C1_C4_ENABLED" ]]; then
    echo "CRON_SYNC_C1_C4_ENABLED not set. Exiting..."
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

django-admin sync_c1_c4
