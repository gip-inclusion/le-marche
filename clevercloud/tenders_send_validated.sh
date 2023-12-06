#!/bin/bash -l

# Send Tenders who are validated but not sent

# Do not run if this env var is not set:
if [[ -z "$CRON_TENDER_SEND_VALIDATED_ENABLED" ]]; then
    echo "CRON_TENDER_SEND_VALIDATED_ENABLED not set. Exiting..."
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

django-admin send_validated_tenders
