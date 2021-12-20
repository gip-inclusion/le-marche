#!/bin/bash -l

# Update API QPV fields for new siaes

# Do not run if this env var is not set:
if [[ -z "$CRON_UPDATE_API_QPV_FIELDS_ENABLED" ]]; then
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

django-admin update_siaes_is_in_qpv
