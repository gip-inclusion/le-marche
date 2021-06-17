FROM python:3.9-slim-buster as base

ENV ENV=PROD \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  HOST=0.0.0.0 \
  PORT=8000

ENV MYSQL_ADDON_DB=${MYSQL_ADDON_DB} \
    MYSQL_ADDON_HOST=${MYSQL_ADDON_HOST} \
    MYSQL_ADDON_PORT=${MYSQL_ADDON_PORT} \
    MYSQL_ADDON_USER=${MYSQL_ADDON_USER} \
    MYSQL_ADDON_PASSWORD=${MYSQL_ADDON_PASSWORD} \
    POSTGRESQL_ADDON_DB=${POSTGRESQL_ADDON_DB} \
    POSTGRESQL_ADDON_HOST=${POSTGRESQL_ADDON_HOST} \
    POSTGRESQL_ADDON_PORT=${POSTGRESQL_ADDON_PORT} \
    POSTGRESQL_ADDON_USER=${POSTGRESQL_ADDON_USER} \
    POSTGRESQL_ADDON_PASSWORD=${POSTGRESQL_ADDON_PASSWORD} \
    SECRET_KEY=${SECRET_KEY} \
    PYTHONPATH=${PYTHONPATH}:/app/lemarche \
    DEBUG=${DEBUG}

WORKDIR /app

COPY install-packages.sh .
RUN ./install-packages.sh

# Multistage build : BUILD
FROM base as builder

# Default arguments
ARG ENV="dev"
ARG MYSQL_ADDON_DB="database" \
    MYSQL_ADDON_HOST="localhost"\
    MYSQL_ADDON_USER="root" \
    MYSQL_ADDON_PORT="3306" \
    MYSQL_ADDON_PASSWORD="[SECRET]" \
    POSTGRESQL_ADDON_DB="database" \
    POSTGRESQL_ADDON_HOST="localhost"\
    POSTGRESQL_ADDON_USER="root" \
    POSTGRESQL_ADDON_PORT="5431" \
    POSTGRESQL_ADDON_PASSWORD="[SECRET]" \
    TRACKER_HOST="http://localhost" \
    DEBUG="False"

ENV PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.1.1 \
  NODE_VERSION=14 \
  TRACKER_HOST=${TRACKER_HOST}

# Install python environment
RUN pip install "poetry==$POETRY_VERSION"
RUN pip install uwsgi

#     apt-get install build-essential -y
COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false && \
    poetry install $(test $ENV == "prod" && echo "--no-dev") --no-interaction --no-ansi

COPY . .

# CMD ["bash"]
CMD ["config/runner.sh"]

# # Multistage build : RUN
# TODO: Make multisage deployment work
#
# FROM base as final
# 
# # CMD ["bash"]
# CMD ["lemarche/runner.sh"]
