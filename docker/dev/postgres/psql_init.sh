#!/bin/bash
set -e

# Initialization script.
# https://hub.docker.com/_/postgres/#initialization-scripts

export BASE_DIR=$(dirname "$BASH_SOURCE")

# The PostgreSQL user should be able to create extensions.
# Only the PostgreSQL superuser role provides that permission.
psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" <<-EOSQL

  \c postgres;

  CREATE USER $LEMARCHE_POSTGRES_USER WITH ENCRYPTED PASSWORD '$LEMARCHE_POSTGRES_PASSWORD';
  CREATE DATABASE $LEMARCHE_POSTGRES_DB OWNER $LEMARCHE_POSTGRES_USER;
  ALTER USER $LEMARCHE_POSTGRES_USER CREATEDB SUPERUSER;

EOSQL
