#!/bin/bash -l

# Find tender without insterested siae and send email to author with top 5 siaes

# Do not run if this env var is not set:
if [[ -z "$CRON_TENDER_SEND_AUTHOR_LIST_OF_SUPER_SIAES_EMAILS_ENABLED" ]]; then
    echo "CRON_TENDER_SEND_AUTHOR_LIST_OF_SUPER_SIAES_EMAILS_ENABLED not set. Exiting..."
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

django-admin send_author_list_of_super_siaes_emails
