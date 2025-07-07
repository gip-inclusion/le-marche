#!/bin/bash -l

# Sync contacts with Brevo CRM

# Do not run if this env var is not set:
if [[ -z "$CRON_CRM_BREVO_SYNC_CONTACTS_ENABLED" ]]; then
    echo "CRON_CRM_BREVO_SYNC_CONTACTS_ENABLED not set. Exiting..."
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

django-admin crm_brevo_sync_contacts --recently-updated
