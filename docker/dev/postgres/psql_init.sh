#!/bin/bash
set -e

# Initialization script.
# https://hub.docker.com/_/postgres/#initialization-scripts

export BASE_DIR=$(dirname "$BASH_SOURCE")

# The PostgreSQL user should be able to create extensions.
# Only the PostgreSQL superuser role provides that permission.
psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" <<-EOSQL

  \c postgres;

  CREATE USER $POSTGRESQL_ADDON_USER WITH ENCRYPTED PASSWORD '$POSTGRESQL_ADDON_PASSWORD';
  CREATE DATABASE $POSTGRESQL_ADDON_DB OWNER $POSTGRESQL_ADDON_USER;
  ALTER USER $POSTGRESQL_ADDON_USER CREATEDB SUPERUSER;

EOSQL
