#!/bin/bash -l

# About clever cloud cronjobs:
# https://developers.clever-cloud.com/doc/administrate/cron/

if [[ "$INSTANCE_NUMBER" != "0" ]]; then
    echo "Instance number is ${INSTANCE_NUMBER}. Stop here."
    exit 0
fi

# $APP_HOME is set by default by clever cloud.
cd $APP_HOME

# Clean old history from more than 180 days ago
# https://django-simple-history.readthedocs.io/en/stable/utils.html#clean-old-history
django-admin clean_old_history --days 180 --auto
