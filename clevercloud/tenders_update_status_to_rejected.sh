#!/bin/bash -l

# Update Tenders' status to rejected if no changes whitin 10 days since modification request

# Do not run if this env var is not set:
if [[ -z "$CRON_TENDER_UPDATE_STATUS_TO_REJECTED_ENABLED" ]]; then
    echo "CRON_TENDER_UPDATE_STATUS_TO_REJECTED_ENABLED not set. Exiting..."
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

django-admin tenders_update_status_to_rejected