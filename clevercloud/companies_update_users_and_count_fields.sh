#!/bin/bash -l

# Update company users

# Do not run if this env var is not set:
if [[ -z "$CRON_UPDATE_COMPANY_USERS_ENABLED" ]]; then
    echo "CRON_UPDATE_COMPANY_USERS_ENABLED not set. Exiting..."
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

django-admin set_company_users --only-add
django-admin update_company_count_fields
