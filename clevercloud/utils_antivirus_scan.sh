#!/bin/bash -l

# Scan S3 files uploaded in tender form for viruses

# Do not run if this env var is not set:
if [[ -z "$CRON_ANTIVIRUS_SCAN_ENABLED" ]]; then
    echo "CRON_ANTIVIRUS_SCAN_ENABLED not set. Exiting..."
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

# Scan every 10 minutes, but only for the last 11 minutes (1 minute overlap to be sure)
django-admin antivirus_scan --minutes-since 11
