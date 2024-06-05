#!/bin/bash -l

# Update Elasticsearch index for semantic search and IA Matching

# Do not run if this env var is not set:
if [[ -z "$CRON_SIAES_SYNC_ELASTICSEARCH_INDEX_ENABLED" ]]; then
    echo "CRON_SIAES_SYNC_ELASTICSEARCH_INDEX_ENABLED not set. Exiting..."
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

django-admin put_siaes_in_elasticsearch_index
