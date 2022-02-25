#!/bin/bash -l

# Send SiaeUserRequest reminders

# Do not run if this env var is not set:
if [[ -z "$CRON_SIAE_SEND_USER_REQUEST_REMINDERS_ENABLED" ]]; then
    echo "CRON_SIAE_SEND_USER_REQUEST_REMINDERS_ENABLED not set. Exiting..."
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

django-admin send_siae_user_request_reminder_emails
