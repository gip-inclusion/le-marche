#!/bin/bash -l

# Update siae super_badge field

# Do not run if this env var is not set:
if [[ -z "$CRON_UPDATE_SIAE_SUPER_BADGE_FIELD_ENABLED" ]]; then
    echo "CRON_UPDATE_SIAE_SUPER_BADGE_FIELD_ENABLED not set. Exiting..."
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

# Run only on the first Monday of each month
django-admin update_siae_super_badge_field --day-of-week 0 --day-of-month first
