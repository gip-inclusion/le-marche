FROM python:3.9-slim-buster as base

ENV ENV=PROD \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  HOST=0.0.0.0 \
  PORT=8000

ENV MYSQL_DB=${MYSQL_DB} \
    MYSQL_HOST=${MYSQL_HOST} \
    MYSQL_PORT=${MYSQL_PORT} \
    MYSQL_USER=${MYSQL_USER} \
    MYSQL_PASSWORD=${MYSQL_PASSWORD} \
    PYTHONPATH=${PYTHONPATH}:/app/itou_c4_api

WORKDIR /app

COPY install-packages.sh .
RUN ./install-packages.sh

# Multistage build : BUILD
FROM base as builder

ARG ENV="dev"
ARG MYSQL_DB="database" \
    MYSQL_HOST="localhost"\
    MYSQL_USER="root" \
    MYSQL_PORT="3306" \
    MYSQL_PASSWORD="[SECRET]"

ENV PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.1.1 \
  NODE_VERSION=14

# Install python environment
RUN pip install "poetry==$POETRY_VERSION"
RUN pip install uwsgi

#     apt-get install build-essential -y
COPY poetry.lock pyproject.toml /app/
COPY . .

RUN poetry config virtualenvs.create false && \
    poetry install $(test $ENV == "prod" && echo "--no-dev") --no-interaction --no-ansi

# CMD ["bash"]
CMD ["itou_c4_api/runner.sh"]

# # Multistage build : RUN
# FROM base as final
# 
# # CMD ["bash"]
# CMD ["itou_c4_api/runner.sh"]
