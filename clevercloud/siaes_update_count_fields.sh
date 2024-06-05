#!/bin/bash -l

# Update siae count fields

# Do not run if this env var is not set:
if [[ -z "$CRON_UPDATE_SIAE_COUNT_FIELDS_ENABLED" ]]; then
    echo "CRON_UPDATE_SIAE_COUNT_FIELDS_ENABLED not set. Exiting..."
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

# django-admin update_siae_count_fields
django-admin update_siae_count_fields --fields etablissement_count --fields completion_rate --fields tender_count --fields tender_email_send_count --fields tender_email_link_click_count --fields tender_detail_display_count --fields tender_detail_contact_click_count
