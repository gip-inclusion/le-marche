# ----------------------------------------------------
# Base-image
# ----------------------------------------------------
FROM python:3.9-slim-buster as common-base
# Django directions: https://blog.ploetzli.ch/2020/efficient-multi-stage-build-django-docker/
# Pip on docker : https://pythonspeed.com/articles/multi-stage-docker-python/
# https://blog.mikesir87.io/2018/07/leveraging-multi-stage-builds-single-dockerfile-dev-prod/
# https://pythonspeed.com/articles/base-image-python-docker-images/

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

WORKDIR /app

COPY install-packages.sh .
RUN ./install-packages.sh

# ----------------------------------------------------
# Install dependencies
# ----------------------------------------------------
FROM common-base AS dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install "poetry==$POETRY_VERSION"
RUN pip install uwsgi 

#     apt-get install build-essential -y
COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false && \
    poetry config virtualenvs.path /opt/venv && \
    poetry install $(test $ENV == "prod" && echo "--no-dev") --no-interaction --no-ansi


# ----------------------------------------------------
# Build project
# ----------------------------------------------------
FROM common-base AS app-run
COPY --from=dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY . .

# ----------------------------------------------------
# Run Dev
# ----------------------------------------------------
FROM app-run AS dev
CMD ["bash"]

# ----------------------------------------------------
# Run Dev
# ----------------------------------------------------
FROM app-run AS prod
CMD ["config/runner.sh"]

# # For some _real_ performance :
# FROM python:3.9-alpine as prod
# COPY --from=dependencies /opt/venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"
# COPY . .
# RUN apk add python3-dev build-base linux-headers pcre-dev
# RUN pip install uwsgi
