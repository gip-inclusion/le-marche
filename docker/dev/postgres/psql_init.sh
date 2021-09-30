#!/bin/bash
set -e

# Initialization script.
# https://hub.docker.com/_/postgres/#initialization-scripts

export BASE_DIR=$(dirname "$BASH_SOURCE")

# The PostgreSQL user should be able to create extensions.
# Only the PostgreSQL superuser role provides that permission.
psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" <<-EOSQL

  \c postgres;

  CREATE USER $POSTGRES_USER WITH ENCRYPTED PASSWORD '$POSTGRES_PASSWORD';
  CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;
  ALTER USER $POSTGRES_USER CREATEDB SUPERUSER;

EOSQL
